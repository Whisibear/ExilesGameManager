"""Reads real guild membership straight from the server's own save file.

Palworld's dedicated-server REST API has no endpoint for guild data at all -
`/v1/api/players` never returns it - so there's no live API to poll. Guild
membership only exists inside the world save (`Level.sav`, Palworld's
compressed GVAS format) in its `GroupSaveDataMap` property.

Parsing a whole save can be slow on a populated world, mostly because of the
per-Pal/per-item/per-foliage-instance decode passes `palworld-save-tools`
does for data this app doesn't care about. Its own CLI documents skipping
those via a reduced `custom_properties` set for exactly this reason - we
register only the one path we need (`GroupSaveDataMap`) and leave everything
else as opaque undecoded bytes, so this only pays for decompressing the file
and walking its property list, not for understanding it.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from palworld_save_tools.archive import FArchiveReader, uuid_reader
from palworld_save_tools.gvas import GvasFile
from palworld_save_tools.palsav import decompress_sav_to_gvas
from palworld_save_tools.paltypes import PALWORLD_CUSTOM_PROPERTIES, PALWORLD_TYPE_HINTS

from app.services import save_import_service

logger = logging.getLogger("egm.guild_service")

_GROUP_MAP_PATH = ".worldSaveData.GroupSaveDataMap"
_REAL_GUILD_TYPE = "EPalGroupType::Guild"

# Re-parsing a big save on every player-list poll would be far too slow -
# guild membership changes rarely enough that a short-lived cache is fine.
_CACHE_TTL_SECONDS = 60.0
_PLM_MAGIC = b"PlM"
_SAVE_HEADER_SIZE = 12

_cache: dict[str, tuple[float, dict[str, str]]] = {}
_locks: dict[str, asyncio.Lock] = {}


def _normalize_uid(value: Any) -> str:
    return str(value).replace("-", "").lower()


def _decompress_level_save(raw: bytes) -> bytes:
    """Decompress both legacy PlZ (zlib) and current PlM (Oodle) saves."""
    if raw[8:11] != _PLM_MAGIC:
        return decompress_sav_to_gvas(raw)[0]

    uncompressed_len = int.from_bytes(raw[0:4], byteorder="little")
    compressed_len = int.from_bytes(raw[4:8], byteorder="little")
    if len(raw) != _SAVE_HEADER_SIZE + compressed_len:
        raise ValueError(
            f"incorrect PlM compressed length: header says {compressed_len}, "
            f"file contains {len(raw) - _SAVE_HEADER_SIZE}"
        )

    import ooz

    decompressed = ooz.decompress(raw[_SAVE_HEADER_SIZE:], uncompressed_len)
    if len(decompressed) != uncompressed_len:
        raise ValueError(f"incorrect PlM uncompressed length: expected {uncompressed_len}, got {len(decompressed)}")
    return decompressed


def _read_player(reader: FArchiveReader, *, with_role: bool = False) -> dict[str, Any]:
    player = {
        "player_uid": reader.guid(),
        "player_info": {
            "last_online_real_time": reader.i64(),
            "player_name": reader.fstring(),
        },
    }
    if with_role:
        reader.byte()
    return player


def _read_guild_tail(reader: FArchiveReader) -> list[dict[str, Any]]:
    start = reader.data.tell()
    try:
        reader.tarray(lambda r: r.byte())  # guild chest roles
        reader.i32()
        reader.guid()  # admin
        players = reader.tarray(lambda r: _read_player(r, with_role=True))
        reader.tarray(lambda r: (r.byte(), r.tarray(lambda nested: nested.byte())))
        reader.byte_list(4)
        if reader.eof():
            return players
    except Exception:
        pass

    reader.data.seek(start)
    reader.guid()  # admin
    players = reader.tarray(_read_player)
    reader.byte_list(4)
    return players


def _decode_group_bytes(parent_reader: FArchiveReader, group_bytes: list[int], group_type: str) -> dict[str, Any]:
    reader = parent_reader.internal_copy(bytes(group_bytes), debug=False)
    group_data: dict[str, Any] = {
        "group_type": group_type,
        "group_id": reader.guid(),
        "group_name": reader.fstring(),
        "individual_character_handle_ids": reader.tarray(lambda r: {"guid": r.guid(), "instance_id": r.guid()}),
    }
    if group_type in {
        "EPalGroupType::Guild",
        "EPalGroupType::IndependentGuild",
        "EPalGroupType::Organization",
    }:
        group_data["org_type"] = reader.byte()
    if group_type == _REAL_GUILD_TYPE:
        reader.byte_list(4)
        reader.tarray(uuid_reader)
        reader.i32()
        reader.i32()
        reader.tarray(uuid_reader)
        group_data["guild_name"] = reader.fstring()
        reader.guid()
        reader.tarray(
            lambda r: (
                r.guid(),
                r.vector_dict(),
                r.i32(),
                r.guid(),
            )
        )
        group_data["players"] = _read_guild_tail(reader)
    return group_data


def _decode_group_map(reader: FArchiveReader, type_name: str, size: int, path: str) -> dict[str, Any]:
    if type_name != "MapProperty":
        raise ValueError(f"expected MapProperty for guild map, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    for group in value["value"]:
        group_type = group["value"]["GroupType"]["value"]["value"]
        group_bytes = group["value"]["RawData"]["value"]["values"]
        group["value"]["RawData"]["value"] = _decode_group_bytes(reader, group_bytes, group_type)
    return value


_CUSTOM_PROPERTIES = {
    _GROUP_MAP_PATH: (
        _decode_group_map,
        PALWORLD_CUSTOM_PROPERTIES[_GROUP_MAP_PATH][1],
    )
}


def _parse_guild_map(level_sav: Path) -> dict[str, str]:
    raw = level_sav.read_bytes()
    gvas_bytes = _decompress_level_save(raw)
    gvas_file = GvasFile.read(gvas_bytes, PALWORLD_TYPE_HINTS, _CUSTOM_PROPERTIES)
    world_save = gvas_file.properties.get("worldSaveData", {}).get("value", {})
    groups = world_save.get("GroupSaveDataMap", {}).get("value", [])

    player_guild: dict[str, str] = {}
    for group in groups:
        raw_data = group.get("value", {}).get("RawData", {}).get("value", {})
        if raw_data.get("group_type") != _REAL_GUILD_TYPE:
            continue
        guild_name = raw_data.get("guild_name")
        if not guild_name:
            continue
        for player in raw_data.get("players", []):
            player_uid = player.get("player_uid")
            if player_uid is None:
                continue
            player_guild[_normalize_uid(player_uid)] = guild_name
    return player_guild


async def _refresh(instance: dict[str, Any]) -> dict[str, str]:
    destination = save_import_service.inspect_destination(instance)
    if not destination:
        return {}
    level_sav = Path(destination["path"]) / "Level.sav"
    if not level_sav.is_file():
        return {}
    try:
        return await asyncio.to_thread(_parse_guild_map, level_sav)
    except Exception as e:
        # Guild display is a nice-to-have, not core functionality - a save
        # mid-write, an unexpected format quirk, or a future Palworld update
        # changing the save layout should never break the player list.
        logger.warning("guild_service: failed to read guild data from %s: %s", level_sav, e)
        return {}


async def get_guild_map(instance: dict[str, Any]) -> dict[str, str]:
    """Returns {normalized player uid: guild name}, refreshed at most once
    every _CACHE_TTL_SECONDS per instance."""
    instance_id = instance["id"]
    now = time.time()
    cached = _cache.get(instance_id)
    if cached and now - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    lock = _locks.setdefault(instance_id, asyncio.Lock())
    async with lock:
        cached = _cache.get(instance_id)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            return cached[1]
        guild_map = await _refresh(instance)
        _cache[instance_id] = (time.time(), guild_map)
        return guild_map


def lookup(guild_map: dict[str, str], player_uid: Any) -> str | None:
    if not player_uid:
        return None
    return guild_map.get(_normalize_uid(player_uid))

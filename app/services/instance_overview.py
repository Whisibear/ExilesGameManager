from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.services import (
    conan_process_manager,
    conan_settings,
    instance_store,
    palworld_settings,
    process_manager,
)


def _latest_palworld_save(server_path: str) -> str:
    root = Path(server_path) / "Pal" / "Saved" / "SaveGames"
    if not root.is_dir():
        return ""
    newest: float | None = None
    try:
        for path in root.rglob("*.sav"):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            newest = mtime if newest is None else max(newest, mtime)
    except OSError:
        return ""
    return datetime.fromtimestamp(newest).isoformat() if newest else ""


def _latest_conan_save(server_path: str) -> str:
    saved = Path(server_path) / "ConanSandbox" / "Saved"
    candidates = [saved / "game.db", saved / "game_0.db"]
    candidates.extend(saved.glob("game_*.db") if saved.is_dir() else [])
    newest: float | None = None
    for path in candidates:
        try:
            if not path.is_file():
                continue
            mtime = path.stat().st_mtime
        except OSError:
            continue
        newest = mtime if newest is None else max(newest, mtime)
    return datetime.fromtimestamp(newest).isoformat() if newest else ""


def build(instance: dict[str, Any]) -> dict[str, Any]:
    game = instance_store.get_game_definition(instance)
    server_path = Path(instance["serverPath"])
    if game.family == "conan_exiles":
        stats = conan_process_manager.get_status(instance)
        max_players = conan_settings.read_max_players(server_path) or 32
        last_saved = _latest_conan_save(instance["serverPath"])
        map_name = instance.get("mapName") or "Exiled Lands"
    else:
        stats = process_manager.get_status(instance["id"])
        max_players = palworld_settings.read_max_players(server_path) or 32
        recorded = process_manager.get_last_saved(instance["id"]) or ""
        disk_saved = _latest_palworld_save(instance["serverPath"])
        last_saved = max(recorded, disk_saved) if recorded and disk_saved else (recorded or disk_saved)
        map_name = instance.get("mapName") or "Palpagos Islands"
    return {
        "id": instance["id"],
        "name": instance["name"],
        "gameId": game.id,
        "gameFamily": game.family,
        "gameLabel": game.label,
        "state": stats["state"],
        "map": map_name,
        "uptimeSeconds": stats["uptimeSeconds"],
        "lastSavedAt": last_saved,
        "playersOnline": 0,
        "maxPlayers": max_players,
        "gamePort": instance_store.resolve_game_port(instance),
        "archived": bool(instance.get("archived")),
    }


def list_all() -> list[dict[str, Any]]:
    return [build(instance) for instance in instance_store.list_instances()]

import asyncio
import sys
import types
from pathlib import Path

# guild_service depends on optional save-decoding packages that are not
# available in every CI environment. The players route only needs these two
# functions for the lifecycle tests below, so provide a narrow test double
# before importing the route module.
guild_service_stub = types.ModuleType("app.services.guild_service")


async def _empty_guild_map(_instance):
    return {}


def _lookup(_guild_map, _player_id):
    return "Unaffiliated"


guild_service_stub.get_guild_map = _empty_guild_map
guild_service_stub.lookup = _lookup
sys.modules.setdefault("app.services.guild_service", guild_service_stub)

from app.routes import players as players_route
from app.services import instance_store, palworld_rest, player_history, process_manager


def _instance(tmp_path: Path) -> dict:
    server_path = tmp_path / "PalServer"
    server_path.mkdir(parents=True)
    return instance_store.create_instance(
        name="Offline Test",
        server_path=str(server_path),
        source="manual",
        game_port=8211,
        rcon_port=8212,
    )


def test_offline_server_returns_persisted_roster_without_rest_call(tmp_path, monkeypatch):
    instance = _instance(tmp_path)
    player_history.sync_online(
        instance["id"],
        [{"userId": "76561198000000000", "playerId": "player-1", "name": "Whisibear", "level": 12}],
    )

    monkeypatch.setattr(process_manager, "get_status", lambda instance_id: {"state": "offline"})

    async def fail_if_called(_instance):
        raise AssertionError("REST API must not be called for an offline server")

    monkeypatch.setattr(palworld_rest, "players", fail_if_called)

    result = asyncio.run(players_route._list_players())

    assert len(result) == 1
    assert result[0]["characterName"] == "Whisibear"
    assert result[0]["connectionStatus"] == "offline"
    assert result[0]["onlineSeconds"] == 0


def test_rest_connection_failure_returns_offline_roster(tmp_path, monkeypatch):
    _instance(tmp_path)
    monkeypatch.setattr(process_manager, "get_status", lambda instance_id: {"state": "online"})

    async def unavailable(_instance):
        raise palworld_rest.PalworldRestConnectionError("temporarily unavailable")

    monkeypatch.setattr(palworld_rest, "players", unavailable)

    result = asyncio.run(players_route._list_players())

    assert result == []

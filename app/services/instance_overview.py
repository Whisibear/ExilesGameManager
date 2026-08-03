from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from app.services import instance_store, palworld_settings, process_manager


def _latest_save(server_path: str) -> str:
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


def build(instance: dict[str, Any]) -> dict[str, Any]:
    stats = process_manager.get_status(instance["id"])
    max_players = palworld_settings.read_max_players(Path(instance["serverPath"])) or 32
    recorded = process_manager.get_last_saved(instance["id"]) or ""
    disk_saved = _latest_save(instance["serverPath"])
    last_saved = max(recorded, disk_saved) if recorded and disk_saved else (recorded or disk_saved)
    return {
        "id": instance["id"],
        "name": instance["name"],
        "state": stats["state"],
        "map": instance.get("mapName") or "Palpagos Islands",
        "uptimeSeconds": stats["uptimeSeconds"],
        "lastSavedAt": last_saved,
        "playersOnline": 0,
        "maxPlayers": max_players,
        "gamePort": instance_store.resolve_game_port(instance),
        "archived": bool(instance.get("archived")),
    }


def list_all() -> list[dict[str, Any]]:
    return [build(i) for i in instance_store.list_instances()]

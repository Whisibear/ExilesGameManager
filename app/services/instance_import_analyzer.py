from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from app.games import is_valid_install
from app.services import instance_store


def _exists_any(paths: list[Path]) -> bool:
    return any(path.is_file() for path in paths)



def _read_ini_port(path: Path, key: str) -> int | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\d+)\s*$", text)
    if not match:
        return None
    value = int(match.group(1))
    return value if 1 <= value <= 65535 else None


def detected_ports(server_root: Path, game: Any) -> dict[str, int]:
    defaults = dict(game.default_ports)
    if game.family != "conan_exiles":
        return {str(key): int(value) for key, value in defaults.items()}

    config_root = server_root / "ConanSandbox" / "Saved" / "Config" / "WindowsServer"
    engine_ini = config_root / "Engine.ini"
    game_ini = config_root / "Game.ini"
    game_port = _read_ini_port(engine_ini, "Port") or int(defaults.get("game", 7777))
    query_port = _read_ini_port(engine_ini, "GameServerQueryPort") or int(defaults.get("query", 27015))
    rcon_port = _read_ini_port(game_ini, "RconPort") or int(defaults.get("rcon", 25575))
    return {
        "game": game_port,
        "pinger": game_port + 1,
        "query": query_port,
        "rcon": rcon_port,
    }


def analyze(instance: dict[str, Any]) -> dict[str, Any]:
    game = instance_store.get_game_definition(instance)
    root = Path(instance["serverPath"])
    issues: list[dict[str, str]] = []
    checks: dict[str, bool] = {
        "installFolder": root.is_dir(),
        "executable": is_valid_install(game, root) if root.is_dir() else False,
    }

    if game.family == "conan_exiles":
        config_root = root / "ConanSandbox" / "Saved" / "Config" / "WindowsServer"
        saved_root = root / "ConanSandbox" / "Saved"
        config_files = [
            config_root / "ServerSettings.ini",
            config_root / "Game.ini",
            config_root / "Engine.ini",
        ]
        save_files = [saved_root / "game.db", saved_root / "game_0.db"]
        if saved_root.is_dir():
            save_files.extend(saved_root.glob("game_*.db"))

        checks["serverConfig"] = _exists_any(config_files)
        checks["saveGame"] = _exists_any(save_files)
        checks["modList"] = (root / "ConanSandbox" / "Mods" / "modlist.txt").is_file()
        checks["workshopLibrary"] = (root / "steamapps" / "workshop" / "content" / "440900").is_dir()

        if not checks["serverConfig"]:
            issues.append({
                "code": "server_config_unavailable",
                "severity": "warning",
                "titleKey": "settings.import.analysis.configUnavailableTitle",
                "messageKey": "settings.import.analysis.configUnavailableMessage",
                "fallbackTitle": "Server Config unavailable",
                "fallbackMessage": "No Conan server configuration was found under ConanSandbox\\Saved\\Config\\WindowsServer. EGM imported the server, but settings cannot be read until Conan creates or restores these files.",
            })
        if not checks["saveGame"]:
            issues.append({
                "code": "savegame_unavailable",
                "severity": "warning",
                "titleKey": "settings.import.analysis.saveUnavailableTitle",
                "messageKey": "settings.import.analysis.saveUnavailableMessage",
                "fallbackTitle": "Server Save unavailable",
                "fallbackMessage": "No Conan game database was found under ConanSandbox\\Saved. This can be normal for a fresh installation; start the server once or restore a backup before expecting existing world data.",
            })
    else:
        config = root / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini"
        saves = root / "Pal" / "Saved" / "SaveGames"
        checks["serverConfig"] = config.is_file()
        checks["saveGame"] = saves.is_dir() and any(path.is_file() for path in saves.rglob("*.sav"))

    return {
        "gameId": game.id,
        "gameFamily": game.family,
        "serverPath": str(root),
        "ready": bool(checks.get("executable")) and not any(issue["severity"] == "error" for issue in issues),
        "checks": checks,
        "ports": detected_ports(root, game),
        "issues": issues,
    }

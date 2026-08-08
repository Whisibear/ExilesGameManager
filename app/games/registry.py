from __future__ import annotations
from pathlib import Path
from app.games.models import GameCapabilities, GameDefinition, PortDefinition

DEFAULT_GAME_ID = "palworld"
_GAMES = {
    "palworld": GameDefinition(
        "palworld","palworld","standard","Palworld","Palworld","available",
        2394010,1623730,None,("PalServer.exe",),
        (PortDefinition("game","Game Port",8211,"UDP"),
         PortDefinition("restApi","REST API Port",8212,"TCP"),
         PortDefinition("query","Steam Query Port",8213,"UDP")),
        GameCapabilities(True,True,True,True,False,False,True,True,True,True,True),
    ),
    "conan_exiles_enhanced": GameDefinition(
        "conan_exiles_enhanced","conan_exiles","enhanced",
        "Conan Exiles Enhanced","Conan Enhanced","available",443030,440900,None,
        ("ConanSandboxServer.exe",
         "ConanSandbox/ConanSandboxServer.exe",
         "ConanSandbox/Binaries/Win64/ConanSandboxServer-Win64-Shipping.exe"),
        (PortDefinition("game","Game Port",7777,"UDP"),
         PortDefinition("pinger","Pinger Port",7778,"UDP",False,"game",1),
         PortDefinition("query","Server Query Port",27015,"UDP"),
         PortDefinition("rcon","RCON Port",25575,"TCP")),
        GameCapabilities(True,True,True,False,True,True,False,False,True,False,True),
    ),
    "conan_exiles_legacy": GameDefinition(
        "conan_exiles_legacy","conan_exiles","legacy",
        "Conan Exiles Legacy","Conan Legacy","available",443030,440900,
        "conan-exiles-legacy",
        ("ConanSandboxServer.exe",
         "ConanSandbox/ConanSandboxServer.exe",
         "ConanSandbox/Binaries/Win64/ConanSandboxServer-Win64-Shipping.exe"),
        (PortDefinition("game","Game Port",7777,"UDP"),
         PortDefinition("pinger","Pinger Port",7778,"UDP",False,"game",1),
         PortDefinition("query","Server Query Port",27015,"UDP"),
         PortDefinition("rcon","RCON Port",25575,"TCP")),
        GameCapabilities(True,True,True,False,True,True,False,False,True,False,True),
    ),
}
def list_games(): return list(_GAMES.values())
def get_game(game_id): return _GAMES.get(str(game_id or "").strip().lower())
def get_game_or_default(game_id): return get_game(game_id or DEFAULT_GAME_ID) or _GAMES[DEFAULT_GAME_ID]
def require_game(game_id):
    game=get_game(game_id)
    if game is None: raise ValueError(f"Unsupported game id: {game_id}")
    return game
def require_deployable_game(game_id):
    game=require_game(game_id)
    if not game.deployable:
        raise ValueError(f"{game.label} is prepared for the multi-game deployment engine but cannot be installed until its runtime provider is complete.")
    return game
def executable_path(game, install_root: Path):
    for candidate in game.executable_candidates:
        path=install_root/Path(candidate)
        if path.is_file(): return path
    return None
def is_valid_install(game, install_root: Path): return executable_path(game, install_root) is not None

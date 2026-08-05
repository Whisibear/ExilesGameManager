from pathlib import Path
from typing import Any

from app.services import instance_storage

_STORE_NAME = "config"

def pal_directory(server_path: str | Path) -> Path:
    path = Path(server_path)
    if path.name.lower() == "pal":
        return path
    if (path / "Binaries" / "Win64").exists():
        return path
    return path / "Pal"


def server_root_directory(server_path: str | Path) -> Path:
    pal = pal_directory(server_path)
    return pal.parent if pal.name.lower() == "pal" else Path(server_path)


def default_mods_path(server_path: str) -> str:
    # UE4SS's mods live under a nested "ue4ss" folder (TICKET-0142/0143) -
    # the older flat Win64/Mods layout is what the legacy stable UE4SS
    # release used, but PalSchema and most current-generation Palworld mods
    # require the Palworld-specific UE4SS fork's newer Win64/ue4ss/Mods
    # layout, and having leftover files at the old flat location actively
    # conflicts with it (see ue4ss_installer.py).
    return str(pal_directory(server_path) / "Binaries" / "Win64" / "ue4ss" / "Mods")


def default_pak_mods_path(server_path: str) -> str:
    # Pak-based content mods (a raw .pak, not a UE4SS Lua/Blueprint mod) are
    # not loaded by UE4SS at all - they're mounted directly by the game's
    # own pak system from this folder (TICKET-0143). The "~" prefix is the
    # convention Palworld/UE modding uses to force this folder's paks to be
    # read before the base game's, so overrides actually take effect.
    return str(pal_directory(server_path) / "Content" / "Paks" / "~mods")


def _get_config(instance_id: str) -> dict[str, Any]:
    return instance_storage.load(instance_id, _STORE_NAME, {"modsPathOverride": None})


def get_mods_path_info(instance: dict[str, Any]) -> dict[str, Any]:
    override = _get_config(instance["id"]).get("modsPathOverride")
    if override:
        return {"path": override, "source": "override"}
    return {"path": default_mods_path(instance["serverPath"]), "source": "derived"}


def get_mods_path(instance: dict[str, Any]) -> str | None:
    return get_mods_path_info(instance)["path"]


def get_pak_mods_path(instance: dict[str, Any]) -> str:
    # Derived only for now, no override - unlike the UE4SS Mods folder, this
    # location isn't something Palworld modding conventions vary on.
    return default_pak_mods_path(instance["serverPath"])


def set_mods_path_override(instance_id: str, path: str) -> None:
    instance_storage.save(instance_id, _STORE_NAME, {"modsPathOverride": path})


def clear_mods_path_override(instance_id: str) -> None:
    instance_storage.save(instance_id, _STORE_NAME, {"modsPathOverride": None})

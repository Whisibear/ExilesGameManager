from __future__ import annotations

import os
import tempfile
from pathlib import Path

SECTION = "PalModSettings"
GLOBAL_KEY = "bGlobalEnableMod"
WORKSHOP_ROOT_KEY = "WorkshopRootDir"
ACTIVE_KEY = "ActiveModList"
CONFIG_VERSION_KEY = "ConfigVersion"


def settings_path(server_path: str | Path) -> Path:
    return Path(server_path) / "Mods" / "PalModSettings.ini"


def workshop_root(server_path: str | Path) -> Path:
    return Path(server_path) / "Mods" / "Workshop"


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8-sig").splitlines()


def active_mods(server_path: str | Path) -> list[str]:
    values: list[str] = []
    for line in _read_lines(settings_path(server_path)):
        stripped = line.strip()
        if not stripped.lower().startswith(f"{ACTIVE_KEY.lower()}="):
            continue
        raw = stripped.split("=", 1)[1]
        values.extend(item.strip() for item in raw.replace(";", ",").split(",") if item.strip())
    return list(dict.fromkeys(values))


def write_active_mods(server_path: str | Path, package_names: list[str]) -> Path:
    path = settings_path(server_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    root = workshop_root(server_path)
    root.mkdir(parents=True, exist_ok=True)
    unique = list(dict.fromkeys(name.strip() for name in package_names if name.strip()))

    lines = [
        f"[{SECTION}]",
        f"{GLOBAL_KEY}={'True' if unique else 'False'}",
        f"{WORKSHOP_ROOT_KEY}={root}",
        *[f"{ACTIVE_KEY}={name}" for name in unique],
        f"{CONFIG_VERSION_KEY}=1.0",
        "",
    ]

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return path


def set_enabled(server_path: str | Path, package_name: str, enabled: bool) -> Path:
    current = active_mods(server_path)
    if enabled and package_name not in current:
        current.append(package_name)
    if not enabled:
        current = [name for name in current if name != package_name]
    return write_active_mods(server_path, current)

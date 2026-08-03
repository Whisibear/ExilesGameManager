import logging
import sys
from pathlib import Path
from typing import Any

from app import storage
from app.paths import install_dir
from app.services import activity_log, instance_store, process_manager, runtime_logging
from app.services.process_manager import ProcessError

logger = logging.getLogger("egm.system_settings")

_STORE_NAME = "system_settings"
_RUN_VALUE_NAME = "ExilesGameManager"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

DEFAULT_ADMIN_PORT = 8000
MIN_ADMIN_PORT = 1024
MAX_ADMIN_PORT = 65535

_DEFAULTS: dict[str, Any] = {
    "bootWithWindows": False,
    "autoStartActiveServer": False,
    "privacyMode": False,
    "adminPort": DEFAULT_ADMIN_PORT,
    "debugLogging": False,
}


def _validate_admin_port(port: int) -> None:
    if not (MIN_ADMIN_PORT <= port <= MAX_ADMIN_PORT):
        raise ValueError(f"Admin panel port must be between {MIN_ADMIN_PORT} and {MAX_ADMIN_PORT}.")


def _load() -> dict[str, Any]:
    saved = storage.load(_STORE_NAME, {})
    return {**_DEFAULTS, **saved}


def _save(config: dict[str, Any]) -> None:
    storage.save(_STORE_NAME, {**_DEFAULTS, **config})


def _startup_target() -> Path:
    packaged = install_dir() / "ExilesGameManager.exe"
    if packaged.is_file():
        return packaged
    return Path(sys.executable).resolve()


def _run_command() -> str:
    target = _startup_target()
    return f'"{target}"'


def _read_run_value() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, _RUN_VALUE_NAME)
            return str(value)
    except FileNotFoundError:
        return None
    except OSError as e:
        logger.warning("system_settings: couldn't read startup run key: %s", e)
        return None


def _write_run_value(enabled: bool) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Windows startup is only available on Windows.")

    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
        if enabled:
            winreg.SetValueEx(key, _RUN_VALUE_NAME, 0, winreg.REG_SZ, _run_command())
        else:
            try:
                winreg.DeleteValue(key, _RUN_VALUE_NAME)
            except FileNotFoundError:
                pass


def get_config() -> dict[str, Any]:
    config = _load()
    return {
        **config,
        "bootWithWindows": _read_run_value() is not None,
    }


def get_admin_port() -> int:
    """Lightweight read of just the configured admin panel port - used at
    process startup (desktop_app.py) and by network.py's firewall/UPnP
    handlers, neither of which need get_config()'s Windows-registry check."""
    return int(_load().get("adminPort", DEFAULT_ADMIN_PORT))


def update_config(
    *, boot_with_windows: bool, auto_start_active_server: bool, privacy_mode: bool, admin_port: int, debug_logging: bool = False
) -> dict[str, Any]:
    _validate_admin_port(admin_port)
    _write_run_value(boot_with_windows)
    config = {
        "bootWithWindows": boot_with_windows,
        "autoStartActiveServer": auto_start_active_server,
        "privacyMode": privacy_mode,
        "adminPort": admin_port,
        "debugLogging": bool(debug_logging),
    }
    _save(config)
    runtime_logging.set_debug(bool(debug_logging))
    return get_config()


def restore_active_server_if_enabled() -> None:
    config = _load()
    if not config.get("autoStartActiveServer"):
        return

    instance = instance_store.get_active()
    if not instance:
        logger.info("system_settings: auto-start skipped, no active server selected")
        return

    try:
        process_manager.start(instance)
    except ProcessError as e:
        logger.info("system_settings: auto-start skipped for %s (%s)", instance["name"], e.message)
        return

    activity_log.log(
        "info",
        instance["name"],
        "Server auto-started because ExilesGameManager launched with recovery enabled.",
    )


def is_debug_logging_enabled() -> bool:
    return bool(_load().get("debugLogging", False))

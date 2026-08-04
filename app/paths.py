"""Resolves where this app reads/writes data, aware of two very different
run modes:

- Dev (`python Palworld_Server.py` / uvicorn --reload): data lives in the
  project's own `data/` folder, same as always.
- Frozen (packaged via PyInstaller into a onefile .exe): the executable
  unpacks itself into a fresh temp folder every launch, so anything written
  under that path (sys._MEIPASS) is gone the moment the process exits. User
  data instead has to live somewhere stable across runs. Installed builds use
  the machine-wide writable %ProgramData%\\ExilesGameManager location, kept
  separate from the read-only program files under Program Files.
  Earlier builds used %LOCALAPPDATA%\\PalworldServerAdmin\\data, then
  briefly a `data` folder inside the install folder itself (TICKET-0123).
  detect_legacy_data_dir()/migrate_data_dir() (TICKET-0130) let the caller
  ask the user whether to carry either of those forward, rather than
  migrating automatically and silently.

Bundled *read-only* resources (the built frontend) are the opposite: those
only ever need to be read from wherever PyInstaller actually extracted them.
"""

import os
import sys
from pathlib import Path

# Sole test-only escape hatch (TICKET-0154): every store (users, instances,
# mods, backups, ...) resolves its base folder through data_dir(), so tests
# point this at a throwaway temp folder instead of ever touching a real
# install's actual data/ - never set in normal use, so production behavior
# (dev or frozen) is completely unaffected.
_TEST_DATA_DIR_ENV = "AUTOPAL_DATA_DIR"

# Historical folder name pre-TICKET-0123/0127 versions used under
# %LOCALAPPDATA%. Must stay exactly "PalworldServerAdmin" - it has to keep
# matching the literal folder name old installs actually used on disk, or
# detect_legacy_data_dir() would silently stop finding anyone's existing
# data. Not related to the app's current ExilesGameManager branding.
_LEGACY_APP_DIR_NAME = "PalworldServerAdmin"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _documents_dir() -> Path:
    """The current user's real Documents folder, honoring redirection (e.g.
    OneDrive) - SHGetFolderPathW/CSIDL_PERSONAL is the standard Win32 way to
    ask for it rather than assuming the plain `~\\Documents` path."""
    try:
        import ctypes

        CSIDL_PERSONAL = 5
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
        if buf.value:
            return Path(buf.value)
    except Exception:
        pass
    return Path.home() / "Documents"


def local_app_data_root() -> Path:
    """Stable per-user application-data root for installed EGM builds."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ExilesGameManager"
    base.mkdir(parents=True, exist_ok=True)
    return base


def program_data_root() -> Path:
    """Machine-wide root reserved for managed dedicated-server installations."""
    base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "ExilesGameManager"
    return base


def config_dir() -> Path:
    path = local_app_data_root() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_dir() -> Path:
    path = local_app_data_root() / "cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = local_app_data_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def oauth_dir() -> Path:
    path = local_app_data_root() / "oauth"
    path.mkdir(parents=True, exist_ok=True)
    return path


def downloads_dir() -> Path:
    path = local_app_data_root() / "downloads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def temp_dir() -> Path:
    path = local_app_data_root() / "temp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def backups_dir() -> Path:
    path = local_app_data_root() / "backups"
    path.mkdir(parents=True, exist_ok=True)
    return path



def ensure_local_app_layout() -> dict[str, Path]:
    """Create and return the complete per-user EGM application-data layout."""
    directories = {
        "root": local_app_data_root(),
        "config": config_dir(),
        "cache": cache_dir(),
        "logs": logs_dir(),
        "oauth": oauth_dir(),
        "downloads": downloads_dir(),
        "temp": temp_dir(),
        "backups": backups_dir(),
        "data": local_app_data_root() / "data",
    }
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)
    return directories

def documents_data_dir() -> Path:
    """Legacy Documents location retained only for migration detection."""
    return _documents_dir() / "ExilesGameManager" / "data"


def default_servers_dir() -> Path:
    """Where new Palworld server deployments go by default (TICKET-0133) - a
    visible sibling of the app's own internal data folder, not nested inside
    it, so a user browsing Documents\\ExilesGameManager can find their actual
    server installs easily. The installer creates this folder immediately on
    install; only affects new deployments, not servers already deployed
    elsewhere (e.g. under the older data\\servers layout, or a manually
    chosen install location)."""
    if is_frozen():
        base = program_data_root() / "Servers"
    else:
        base = Path(__file__).resolve().parent.parent / "data" / "servers"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _legacy_appdata_data_dir() -> Path:
    import os

    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / _LEGACY_APP_DIR_NAME / "data"


def _legacy_install_folder_data_dir() -> Path:
    # TICKET-0123's short-lived "data lives inside the install folder" era.
    return install_dir() / "data"


def detect_legacy_data_dir() -> Path | None:
    """Looks for real data from an older version, without touching anything.
    Checks TICKET-0123's install-folder location first, then the original
    pre-0123 %LOCALAPPDATA% location. Returns None if neither has anything -
    including on a fresh install, or once a previous launch has already
    resolved this (see documents_data_dir())."""
    if not is_frozen():
        return None
    for candidate in (
        _legacy_install_folder_data_dir(),
        program_data_root() / "data",
        documents_data_dir(),
        _legacy_appdata_data_dir(),
    ):
        if candidate.is_dir():
            return candidate
    return None


def migrate_data_dir(legacy_dir: Path) -> Path:
    """Moves a legacy data folder (as found by detect_legacy_data_dir()) into
    the current ProgramData-based location. Caller's responsibility to only
    call this after the user has actually agreed to it.

    Uses safe_replace_dir() rather than a plain shutil.move(). A real
    dedicated server's data (game binaries plus save files) can be several
    GB, and shutil.move() falls back to copytree()+rmtree() whenever a plain
    rename() isn't possible (different drive, OneDrive-redirected Documents,
    a locked file, ...) - if that copy is interrupted (killed, crashed, a
    file briefly locked by antivirus), it can leave documents_data_dir()
    half-populated. Since data_dir()/desktop_app.py only check whether that
    folder *exists* to decide "migration already happened, don't ask again",
    a half-populated folder was permanently mistaken for a completed
    migration with no way to retry. safe_replace_dir() instead copies to a
    temp sibling and verifies it first - documents_data_dir() only ever gets
    created at all once the copy is confirmed complete, so an interrupted
    attempt leaves nothing behind and the next launch offers this again.
    The legacy folder itself is only removed after that verified copy
    succeeds, so it's never at risk of being left half-deleted either.
    """
    from app.services import safe_replace

    new_dir = local_app_data_root() / "data"
    safe_replace.safe_replace_dir(legacy_dir, new_dir)

    import shutil

    shutil.rmtree(legacy_dir, ignore_errors=True)
    return new_dir


def data_dir() -> Path:
    override = os.environ.get(_TEST_DATA_DIR_ENV)
    if override:
        base = Path(override)
    elif is_frozen():
        base = local_app_data_root() / "data"
    else:
        base = Path(__file__).resolve().parent.parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def resource_dir() -> Path:
    """Base directory for bundled read-only resources (e.g. the built frontend)."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent.parent


def install_dir() -> Path:
    """The real, stable folder the installer put ExilesGameManager.exe in -
    NOT the same as resource_dir(), which for a frozen onefile build is a
    fresh temp extraction folder that's gone the moment the process exits.
    This is where the installer writes its one-time first-run seed file, so
    the app has to look in the same stable place to find it."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

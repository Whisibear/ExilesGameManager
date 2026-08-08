"""Packaged Windows entry point for Exiles Game Manager.

The frozen application owns the FastAPI backend and a native Windows system-tray
icon. Closing a browser tab never terminates EGM. The tray Quit/Beenden action
performs a graceful Uvicorn shutdown and intentionally leaves managed game-server
processes running.
"""

from __future__ import annotations

import locale
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Final

BIND_HOST: Final = "0.0.0.0"
LOCAL_HOST: Final = "127.0.0.1"
QUIT_EVENT_NAME: Final = r"Local\ExilesGameManager.Quit"


class _Tee:
    def __init__(self, *streams):
        self._streams = [stream for stream in streams if stream is not None]
        self._primary = self._streams[0] if self._streams else None

    def write(self, text: str) -> int:
        for stream in self._streams:
            stream.write(text)
            stream.flush()
        return len(text)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()

    def isatty(self) -> bool:
        return bool(self._primary and self._primary.isatty())

    def fileno(self) -> int:
        if not self._primary:
            raise OSError("No console stream available.")
        return self._primary.fileno()

    @property
    def encoding(self) -> str | None:
        return getattr(self._primary, "encoding", None)

    @property
    def errors(self) -> str | None:
        return getattr(self._primary, "errors", None)

    def __getattr__(self, name: str):
        if not self._primary:
            raise AttributeError(name)
        return getattr(self._primary, name)


def _tee_console_streams() -> None:
    from app.paths import data_dir

    try:
        log_path = data_dir() / "backend.log"
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        import io

        log_file = io.StringIO()
    sys.stdout = _Tee(sys.stdout, log_file)
    sys.stderr = _Tee(sys.stderr, log_file)


_MB_ICONERROR = 0x10
_MB_ICONINFORMATION = 0x40
_MB_ICONQUESTION = 0x20
_MB_YESNO = 0x4
_IDYES = 6


def _show_message_box(message: str, icon: int = _MB_ICONERROR) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, "Exiles Game Manager", icon)
    except Exception:
        pass


def _ask_yes_no(message: str) -> bool:
    try:
        import ctypes

        result = ctypes.windll.user32.MessageBoxW(
            0,
            message,
            "Exiles Game Manager",
            _MB_YESNO | _MB_ICONQUESTION,
        )
        return result == _IDYES
    except Exception:
        return False


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.5)
        return connection.connect_ex((host, port)) == 0


def _offer_legacy_data_migration() -> None:
    from app import paths

    if (paths.program_data_root() / "data").exists():
        return

    legacy_dir = paths.detect_legacy_data_dir()
    if legacy_dir is None:
        return

    migrate = _ask_yes_no(
        "Exiles Game Manager found existing data from a previous install:\n\n"
        f"{legacy_dir}\n\n"
        "Move it into the current EGM ProgramData folder and keep your existing servers, accounts, and mods?\n\n"
        'Choose "No" to leave that data where it is and start with a brand new, empty setup instead.'
    )
    if migrate:
        _show_message_box(
            "Moving your existing data now. This can take a few minutes for a large server - please wait "
            "for the confirmation message and don't close this window, even if it looks like nothing is happening.",
            icon=_MB_ICONINFORMATION,
        )
        try:
            new_dir = paths.migrate_data_dir(legacy_dir)
        except Exception as exc:
            _show_message_box(
                "Moving your existing data failed, so nothing was changed - your original data is still "
                f"intact at:\n\n{legacy_dir}\n\nDetails: {exc}\n\nYou'll be asked again next time you start "
                "Exiles Game Manager."
            )
            return
        _show_message_box(
            f"Your existing data was moved to:\n\n{new_dir}\n\nEverything was carried over automatically.",
            icon=_MB_ICONINFORMATION,
        )
    else:
        paths.data_dir()


def _tray_language() -> str:
    try:
        language = (locale.getlocale()[0] or "").lower()
    except Exception:
        language = ""
    if language.startswith("de"):
        return "de"
    if language.startswith("es"):
        return "es"
    if language.startswith("fr"):
        return "fr"
    if language.startswith("ja"):
        return "ja"
    if language.startswith("zh"):
        return "zh"
    return "en"


_TRAY_TEXT = {
    "en": {
        "title": "Exiles Game Manager",
        "open": "Open Exiles Game Manager",
        "dashboard": "Open Dashboard",
        "running": "EGM backend is running",
        "quit": "Quit",
    },
    "de": {
        "title": "Exiles Game Manager",
        "open": "Exiles Game Manager öffnen",
        "dashboard": "Dashboard öffnen",
        "running": "EGM-Backend läuft",
        "quit": "Beenden",
    },
    "es": {
        "title": "Exiles Game Manager",
        "open": "Abrir Exiles Game Manager",
        "dashboard": "Abrir panel",
        "running": "El backend de EGM está activo",
        "quit": "Salir",
    },
    "fr": {
        "title": "Exiles Game Manager",
        "open": "Ouvrir Exiles Game Manager",
        "dashboard": "Ouvrir le tableau de bord",
        "running": "Le backend EGM est actif",
        "quit": "Quitter",
    },
    "ja": {
        "title": "Exiles Game Manager",
        "open": "Exiles Game Manager を開く",
        "dashboard": "ダッシュボードを開く",
        "running": "EGM バックエンドは実行中です",
        "quit": "終了",
    },
    "zh": {
        "title": "Exiles Game Manager",
        "open": "打开 Exiles Game Manager",
        "dashboard": "打开仪表板",
        "running": "EGM 后端正在运行",
        "quit": "退出",
    },
}


def _tray_icon_image():
    from PIL import Image

    candidates = [
        Path(sys.executable).with_name("ExilesGameManager.ico"),
        Path(__file__).resolve().with_name("ExilesGameManager.ico"),
    ]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "ExilesGameManager.ico")
    for candidate in candidates:
        if candidate.is_file():
            try:
                return Image.open(candidate).convert("RGBA")
            except Exception:
                continue
    return Image.new("RGBA", (64, 64), (30, 35, 45, 255))


def _create_named_quit_event(stop_callback):
    if os.name != "nt":
        return None
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateEventW(None, True, False, QUIT_EVENT_NAME)
        if not handle:
            return None

        def waiter() -> None:
            wait_object_0 = 0
            infinite = 0xFFFFFFFF
            result = kernel32.WaitForSingleObject(handle, infinite)
            if result == wait_object_0:
                stop_callback()
            kernel32.CloseHandle(handle)

        threading.Thread(target=waiter, daemon=True, name="egm-quit-event").start()
        return handle
    except Exception:
        return None


def _run_packaged_server_with_tray(url: str, port: int) -> None:
    import pystray
    import uvicorn

    from app.main import app

    config = uvicorn.Config(app, host=BIND_HOST, port=port, log_level="info")
    server = uvicorn.Server(config)
    stopping = threading.Event()
    icon_holder: dict[str, pystray.Icon] = {}

    def request_shutdown() -> None:
        if stopping.is_set():
            return
        stopping.set()
        server.should_exit = True
        tray_icon = icon_holder.get("icon")
        if tray_icon is not None:
            try:
                tray_icon.stop()
            except Exception:
                pass

    _create_named_quit_event(request_shutdown)

    server_thread = threading.Thread(target=server.run, daemon=False, name="egm-uvicorn")
    server_thread.start()

    language = _tray_language()
    text = _TRAY_TEXT[language]

    def open_app(_icon=None, _item=None) -> None:
        webbrowser.open(url)

    menu = pystray.Menu(
        pystray.MenuItem(text["open"], open_app, default=True),
        pystray.MenuItem(text["dashboard"], open_app),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(text["running"], None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(text["quit"], lambda _icon, _item: request_shutdown()),
    )
    tray_icon = pystray.Icon("ExilesGameManager", _tray_icon_image(), text["title"], menu)
    icon_holder["icon"] = tray_icon

    def stop_tray_if_backend_exits() -> None:
        server_thread.join()
        if not stopping.is_set():
            stopping.set()
            try:
                tray_icon.stop()
            except Exception:
                pass

    threading.Thread(
        target=stop_tray_if_backend_exits,
        daemon=True,
        name="egm-backend-monitor",
    ).start()

    if os.environ.get("EGM_SUPPRESS_BROWSER") != "1":
        def open_browser_when_ready() -> None:
            for _ in range(120):
                if stopping.is_set():
                    return
                if _port_in_use(LOCAL_HOST, port):
                    webbrowser.open(url)
                    return
                time.sleep(0.25)

        threading.Thread(target=open_browser_when_ready, daemon=True, name="egm-browser-open").start()

    try:
        tray_icon.run()
    finally:
        request_shutdown()
        server_thread.join(timeout=20)
        if server_thread.is_alive():
            server.force_exit = True
            server_thread.join(timeout=5)


def main() -> None:
    _offer_legacy_data_migration()
    _tee_console_streams()

    from app.services import system_settings

    port = system_settings.get_admin_port()
    url = f"http://{LOCAL_HOST}:{port}/"
    suppress_browser = os.environ.get("EGM_SUPPRESS_BROWSER") == "1"

    if _port_in_use(LOCAL_HOST, port):
        if not suppress_browser:
            webbrowser.open(url)
        return

    try:
        if os.name == "nt" and os.environ.get("EGM_SUPPRESS_TRAY") != "1":
            _run_packaged_server_with_tray(url, port)
            return

        import uvicorn

        from app.main import app

        if not suppress_browser:
            def open_browser_when_ready() -> None:
                for _ in range(60):
                    if _port_in_use(LOCAL_HOST, port):
                        webbrowser.open(url)
                        return
                    time.sleep(0.25)

            threading.Thread(target=open_browser_when_ready, daemon=True).start()
        uvicorn.run(app, host=BIND_HOST, port=port, log_level="info")
    except Exception:
        traceback.print_exc()
        from app.paths import data_dir

        _show_message_box(
            "Exiles Game Manager couldn't start.\n\n"
            f"Details were written to:\n{data_dir() / 'backend.log'}"
        )
        raise


if __name__ == "__main__":
    main()

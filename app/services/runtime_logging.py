from __future__ import annotations

import io
import json
import logging
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, TextIO

from app import paths

_LOCK = threading.RLock()
_CONFIGURED = False
_SESSION_ID = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def logs_root() -> Path:
    """Return the single user-visible EGM log directory.

    Installed builds keep support-relevant logs under the current user's
    LocalAppData EGM directory. Development builds retain project-local logs.
    """
    base = paths.logs_dir() if paths.is_frozen() else paths.install_dir() / "logs"
    for name in (
        "backend",
        "frontend",
        "audit",
        "application",
        "activity",
        "taskqueue",
        "installer",
        "updater",
        "steamcmd",
        "diagnostics",
    ):
        (base / name).mkdir(parents=True, exist_ok=True)

    guide = base / "README.txt"
    if not guide.exists():
        try:
            guide.write_text(
                "Exiles Game Manager logs\n"
                "=========================\n\n"
                "backend     - backend and console output\n"
                "frontend    - browser/frontend errors\n"
                "audit       - HTTP request audit\n"
                "application - application warnings and errors\n"
                "activity    - server activity shown in the sidebar\n"
                "taskqueue   - complete task queue snapshot\n"
                "installer   - setup and prerequisite installation logs\n"
                "updater     - update-related logs\n"
                "steamcmd    - SteamCMD logs and raw SteamCMD log junction\n"
                "diagnostics - exported diagnostic packages\n",
                encoding="utf-8",
            )
        except OSError:
            pass
    return base


def backend_log_path() -> Path:
    return logs_root() / "backend" / f"egm-backend-{_SESSION_ID}.log"


def backend_console_log_path() -> Path:
    return logs_root() / "backend" / f"egm-console-{_SESSION_ID}.log"


def http_audit_path() -> Path:
    return logs_root() / "audit" / f"egm-http-{_SESSION_ID}.jsonl"


def frontend_log_path() -> Path:
    return logs_root() / "frontend" / f"egm-frontend-{_SESSION_ID}.log"


class _TimestampFormatter(logging.Formatter):
    converter = time.localtime

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        created = datetime.fromtimestamp(record.created).astimezone()
        return created.strftime("%Y-%m-%d %H:%M:%S") + f".{int(record.msecs):03d}"


class TimestampedTee(io.TextIOBase):
    """Mirrors stdout/stderr unchanged to the console and writes complete,
    timestamped lines to a session log. This also captures output printed by
    third-party save parsers that do not use Python's logging module."""

    def __init__(self, stream: TextIO, path: Path, label: str):
        self._stream = stream
        self._path = path
        self._label = label
        self._buffer = ""
        path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def encoding(self) -> str:
        return getattr(self._stream, "encoding", "utf-8") or "utf-8"

    def isatty(self) -> bool:
        return bool(getattr(self._stream, "isatty", lambda: False)())

    def fileno(self) -> int:
        return self._stream.fileno()

    def write(self, text: str) -> int:
        if not text:
            return 0
        self._stream.write(text)
        self._stream.flush()
        with _LOCK:
            self._buffer += text
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                self._append(line.rstrip("\r"))
        return len(text)

    def flush(self) -> None:
        self._stream.flush()
        with _LOCK:
            if self._buffer:
                self._append(self._buffer.rstrip("\r"))
                self._buffer = ""

    def _append(self, line: str) -> None:
        timestamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(f"[{timestamp}] [{self._label}] {line}\n")
        except OSError:
            pass


def install_console_capture() -> Path:
    path = backend_console_log_path()
    if not isinstance(sys.stdout, TimestampedTee):
        sys.stdout = TimestampedTee(sys.stdout, path, "STDOUT")
    if not isinstance(sys.stderr, TimestampedTee):
        sys.stderr = TimestampedTee(sys.stderr, path, "STDERR")
    return path


def configure_logging(debug: bool = False) -> Path:
    global _CONFIGURED
    path = backend_log_path()
    root = logging.getLogger()
    level = logging.DEBUG if debug else logging.INFO
    root.setLevel(level)

    if not any(getattr(handler, "_egm_runtime_file", False) for handler in root.handlers):
        handler = RotatingFileHandler(path, maxBytes=10 * 1024 * 1024, backupCount=7, encoding="utf-8")
        handler._egm_runtime_file = True  # type: ignore[attr-defined]
        handler.setLevel(level)
        handler.setFormatter(_TimestampFormatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            if getattr(handler, "_egm_runtime_file", False):
                handler.setLevel(level)

    logging.captureWarnings(True)
    logging.getLogger("httpx").setLevel(logging.DEBUG if debug else logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.DEBUG if debug else logging.WARNING)
    _CONFIGURED = True
    return path


def set_debug(enabled: bool) -> None:
    configure_logging(enabled)
    logging.getLogger().setLevel(logging.DEBUG if enabled else logging.INFO)


def write_http_event(payload: dict[str, Any]) -> None:
    path = http_audit_path()
    safe = {**payload, "timestamp": datetime.now(timezone.utc).isoformat()}
    try:
        with _LOCK, path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def log_unhandled_exception(exc_type: type[BaseException], exc: BaseException, tb: Any) -> None:
    logging.getLogger("egm.crash").critical(
        "Unhandled exception\n%s", "".join(traceback.format_exception(exc_type, exc, tb))
    )
    sys.__excepthook__(exc_type, exc, tb)

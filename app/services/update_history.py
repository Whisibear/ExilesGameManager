"""Persistent application-update audit trail for EGM."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.paths import (
    last_update_result_path,
    update_history_path,
    update_runtime_log_path,
)

_LOCK = threading.RLock()
_MAX_HISTORY_ENTRIES = 200


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_runtime_log(level: str, message: str, **details: Any) -> None:
    line = {
        "timestamp": _utc_now(),
        "level": level.upper(),
        "message": message,
        "details": details,
    }
    path = update_runtime_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")


def _read_history() -> list[dict[str, Any]]:
    path = update_history_path()
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def append_history(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    normalized.setdefault("recordedAt", _utc_now())
    with _LOCK:
        history = _read_history()
        history.append(normalized)
        history = history[-_MAX_HISTORY_ENTRIES:]
        path = update_history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(history, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        last_update_result_path().write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return normalized


def list_history() -> list[dict[str, Any]]:
    with _LOCK:
        return list(reversed(_read_history()))


def last_result() -> dict[str, Any] | None:
    path = last_update_result_path()
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None

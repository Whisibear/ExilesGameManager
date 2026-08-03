"""Persistent, operator-focused ExilesGameManager application log.

This is deliberately separate from Server Activity. It records the panel/backend
itself and suppresses repetitive polling/access noise. Entries survive restarts
as JSON Lines and as a human-readable daily text file.
"""
from __future__ import annotations

import json
import re
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.services import runtime_logging

LogLevel = Literal["info", "warning", "error", "debug"]
_MAX_ENTRIES = 1000
_LOCK = threading.RLock()
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _jsonl_path() -> Path:
    return runtime_logging.logs_root() / "application" / "app_log.jsonl"


def _daily_path(timestamp: datetime) -> Path:
    path = runtime_logging.logs_root() / "application"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"exilesgamemanager-{timestamp:%Y-%m-%d}.log"


def _normalise_level(level: str) -> LogLevel:
    value = level.lower()
    if value in {"warning", "warn"}:
        return "warning"
    if value in {"error", "critical", "exception"}:
        return "error"
    if value == "debug":
        return "debug"
    return "info"


def log(level: str, component: str, message: str, **details: Any) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    if component.casefold().startswith("frontend: unhandledrejection"):
        try:
            from app.services import task_queue
            recent = task_queue.list_tasks(limit=20)
            if any(
                task.get("status") == "failed"
                and str(task.get("error") or "").strip() == str(message).strip()
                and now.timestamp() - float(task.get("finishedAt") or 0) < 30
                for task in recent
            ):
                return {"deduplicated": True}
        except Exception:
            pass
    entry = {
        "id": uuid.uuid4().hex,
        "timestamp": now.isoformat(),
        "level": _normalise_level(level),
        "source": component or "ExilesGameManager",
        "message": str(message).strip(),
    }
    if details:
        entry["details"] = details

    with _LOCK:
        jsonl = _jsonl_path()
        jsonl.parent.mkdir(parents=True, exist_ok=True)
        try:
            with jsonl.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            with _daily_path(now).open("a", encoding="utf-8") as handle:
                local = now.astimezone()
                handle.write(
                    f"[{local:%Y-%m-%d %H:%M:%S}] [{entry['level'].upper()}] "
                    f"[{entry['source']}] {entry['message']}\n"
                )
        except OSError:
            # Logging must never take down the backend.
            pass
    if entry["level"] in {"warning", "error"}:
        try:
            from app.services import notification_center
            notification_center.publish(
                "error" if entry["level"] == "error" else "warning",
                f"notifications.application.{entry['level']}.title",
                "notifications.application.event.message",
                params={"component": entry["source"], "message": entry["message"]},
                category="application", audience="super_admin",
                fallback_title=f"{entry['source']}: {entry['level'].title()}", fallback_message=entry["message"], action_url="/activity",
            )
        except Exception:
            pass
    return entry


def get_all(limit: int = 500, mask_ips: bool = False) -> list[dict[str, Any]]:
    path = _jsonl_path()
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, min(limit, _MAX_ENTRIES)) :]
    except OSError:
        return []
    for line in reversed(lines):
        try:
            item = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(item, dict):
            if str(item.get("source") or "").casefold() == "palworld_admin.app_update":
                item = dict(item)
                item["source"] = "egm.app_update"
            if mask_ips:
                item = dict(item)
                item["message"] = _IPV4_RE.sub("•.•.•.•", str(item.get("message", "")))
            entries.append(item)
    return entries


class AppEventHandler(logging.Handler):
    """Bridge Python warnings/errors into the operator log without request spam."""

    _NOISY_LOGGERS = ("uvicorn.access", "httpx", "httpcore", "asyncio")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # Routine HTTP/access lines are implementation detail. Keep only warnings/errors.
            if record.name.startswith(self._NOISY_LOGGERS) and record.levelno < logging.WARNING:
                return
            level = _normalise_level(record.levelname)
            message = self.format(record)
            log(level, record.name, message)
        except Exception:
            self.handleError(record)


def install_logging_bridge() -> None:
    root = logging.getLogger()
    if any(isinstance(handler, AppEventHandler) for handler in root.handlers):
        return
    handler = AppEventHandler(level=logging.WARNING)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)

    # Keep the console useful too: no status/metrics polling and no httpx 200 spam.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

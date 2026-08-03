"""Real activity feed behind the Logs page - not Palworld's own console text
(confirmed unreachable: no stdout output, no log file even with -log passed,
and the console itself turned out to be a Dear ImGui overlay rather than a
real text buffer - see memory/decisions.md), but real events this app
already knows about or performs directly: server start/stop, player
join/leave, kick/ban, and scheduled automation firing.

Persisted as JSON Lines (data_dir()/activity_log.jsonl) so history survives
an app restart, not just kept in memory - capped and periodically trimmed
so it doesn't grow forever.
"""

import json
import logging
import threading
import uuid
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from app.paths import data_dir
from app.services import runtime_logging

logger = logging.getLogger("egm.activity_log")

LogLevel = Literal["info", "warning", "error", "debug"]

_MAX_ENTRIES = 2000
_TRIM_CHECK_EVERY = 50
_TRIM_FILE_SIZE_BYTES = 2_000_000

_lock = threading.Lock()
_entries: deque[dict[str, Any]] = deque(maxlen=_MAX_ENTRIES)
_loaded = False
_writes_since_trim = 0


def _log_path() -> Path:
    return runtime_logging.logs_root() / "activity" / "activity_log.jsonl"


def _daily_text_log_path(timestamp: datetime) -> Path:
    path = runtime_logging.logs_root() / "activity"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"server-activity-{timestamp:%Y-%m-%d}.log"


def _load_once() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    path = _log_path()
    if not path.is_file():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines[-_MAX_ENTRIES:]:
        try:
            _entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue


def _trim_file_if_needed() -> None:
    global _writes_since_trim
    _writes_since_trim += 1
    if _writes_since_trim < _TRIM_CHECK_EVERY:
        return
    _writes_since_trim = 0
    path = _log_path()
    try:
        if path.stat().st_size < _TRIM_FILE_SIZE_BYTES:
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(lines[-_MAX_ENTRIES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def _resolve_instance_id(source: str) -> str | None:
    """Resolve the immutable instance id for server-scoped activity.

    Call sites historically passed the display name as ``source``. Keeping the
    public log() signature compatible avoids touching every service, while new
    entries still become stable across instance switches and later renames.
    """
    try:
        from app.services import instance_store

        matches = [
            instance for instance in instance_store.list_instances()
            if str(instance.get("name", "")).casefold() == str(source).casefold()
        ]
        return matches[0].get("id") if len(matches) == 1 else None
    except Exception:
        return None


def log(level: LogLevel, source: str, message: str, *, instance_id: str | None = None) -> None:
    with _lock:
        _load_once()
        now = datetime.now()
        resolved_instance_id = instance_id or _resolve_instance_id(source)
        entry = {
            "id": uuid.uuid4().hex,
            "timestamp": now.isoformat(),
            "level": level,
            "source": source,
            "message": message,
            "instanceId": resolved_instance_id,
        }
        _entries.append(entry)
        try:
            with open(_log_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            with open(_daily_text_log_path(now), "a", encoding="utf-8") as f:
                f.write(f"[{now:%Y-%m-%d %H:%M:%S}] [{level.upper()}] [{source}] {message}\n")
            _trim_file_if_needed()
        except OSError:
            logger.warning("activity_log: couldn't persist entry to disk")

        if level in {"warning", "error"}:
            try:
                from app.services import notification_center
                notification_center.publish(
                    "error" if level == "error" else "warning",
                    f"notifications.server.{level}.title",
                    "notifications.server.event.message",
                    params={"server": source, "message": message},
                    instance_id=resolved_instance_id, category="server",
                    fallback_title=f"{source}: {level.title()}", fallback_message=message, action_url="/activity",
                )
            except Exception:
                logger.debug("Could not publish activity notification", exc_info=True)


def get_all() -> list[dict[str, Any]]:
    """Newest first, matching how the Logs page has always displayed them."""
    with _lock:
        _load_once()
        return list(reversed(_entries))


def get_for_instance(instance_id: str | None) -> list[dict[str, Any]]:
    """Return activity only for the selected server instance.

    New records are keyed by immutable ``instanceId``. Records written by older
    ExilesGameManager builds did not contain that field, so they are migrated at
    read time by matching the then-recorded source name to the selected
    instance. This prevents Test/Test2 activity from leaking into each other
    without discarding existing history.
    """
    if not instance_id:
        return []

    try:
        from app.services import instance_store

        instance = instance_store.get(instance_id)
    except Exception:
        instance = None
    if not instance:
        return []

    instance_name = str(instance.get("name", "")).casefold()
    with _lock:
        _load_once()
        result: list[dict[str, Any]] = []
        for entry in reversed(_entries):
            entry_instance_id = entry.get("instanceId")
            if entry_instance_id == instance_id:
                result.append(entry)
            elif not entry_instance_id and str(entry.get("source", "")).casefold() == instance_name:
                result.append(entry)
        return result

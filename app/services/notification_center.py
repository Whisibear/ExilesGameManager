"""Persistent in-app notification center for Exiles Game Manager."""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.paths import data_dir

_LOCK = threading.RLock()
_MAX_ITEMS = 2000


def _path() -> Path:
    return data_dir() / "notifications.json"


def _load() -> list[dict[str, Any]]:
    path = _path()
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("notifications", []) if isinstance(payload, dict) else []
        return [dict(row) for row in rows if isinstance(row, dict) and row.get("id")]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"version": 1, "notifications": rows[-_MAX_ITEMS:]}, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def publish(
    kind: str,
    title_key: str,
    message_key: str | None = None,
    *,
    params: dict[str, Any] | None = None,
    instance_id: str | None = None,
    category: str = "system",
    audience: str = "all",
    fallback_title: str = "Notification",
    fallback_message: str = "",
    action_url: str | None = None,
) -> dict[str, Any]:
    now = time.time()
    item = {
        "id": f"notification-{uuid.uuid4().hex}",
        "kind": kind if kind in {"success", "info", "warning", "error"} else "info",
        "titleKey": title_key,
        "messageKey": message_key,
        "params": params or {},
        "fallbackTitle": fallback_title,
        "fallbackMessage": fallback_message,
        "instanceId": instance_id,
        "category": category,
        "audience": audience,
        "actionUrl": action_url,
        "createdAt": now,
        "readBy": [],
    }
    with _LOCK:
        rows = _load()
        # Suppress exact duplicate events emitted by overlapping callbacks.
        for previous in reversed(rows[-25:]):
            if now - float(previous.get("createdAt") or 0) > 2.0:
                break
            if all(previous.get(key) == item.get(key) for key in ("kind", "titleKey", "messageKey", "instanceId", "category")) and previous.get("params") == item.get("params"):
                return previous
        rows.append(item)
        _save(rows)
    return item


def _visible(item: dict[str, Any], role: str) -> bool:
    return item.get("audience") != "super_admin" or role == "super_admin"


def list_notifications(username: str, role: str, *, unread_only: bool = False, limit: int = 100) -> list[dict[str, Any]]:
    with _LOCK:
        rows = _load()
    visible = [row for row in rows if _visible(row, role)]
    if unread_only:
        visible = [row for row in visible if username not in row.get("readBy", [])]
    visible.sort(key=lambda row: float(row.get("createdAt") or 0), reverse=True)
    result=[]
    for row in visible[:max(1, min(limit, 500))]:
        item=dict(row)
        item["read"] = username in row.get("readBy", [])
        item.pop("readBy", None)
        result.append(item)
    return result


def unread_count(username: str, role: str) -> int:
    return len(list_notifications(username, role, unread_only=True, limit=500))


def mark_read(notification_id: str, username: str) -> bool:
    changed=False
    with _LOCK:
        rows=_load()
        for item in rows:
            if item.get("id") == notification_id:
                readers=item.setdefault("readBy", [])
                if username not in readers:
                    readers.append(username); changed=True
                break
        if changed: _save(rows)
    return changed


def mark_all_read(username: str, role: str) -> int:
    count=0
    with _LOCK:
        rows=_load()
        for item in rows:
            if not _visible(item, role): continue
            readers=item.setdefault("readBy", [])
            if username not in readers:
                readers.append(username); count += 1
        if count: _save(rows)
    return count


def clear_read(username: str, role: str) -> int:
    with _LOCK:
        rows=_load(); kept=[]; removed=0
        for item in rows:
            if _visible(item, role) and username in item.get("readBy", []): removed += 1
            else: kept.append(item)
        if removed: _save(kept)
    return removed

"""Unified activity timeline across application, server and task events."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services import activity_log, app_event_log, task_queue


_SOURCE_LABELS = {
    "egm.app_update": ("EGM Update Service", "activityCenter.sources.egmUpdateService"),
    "egm.update_service": ("EGM Update Service", "activityCenter.sources.egmUpdateService"),
    "backend": ("Backend Service", "activityCenter.sources.backendService"),
    "workshop": ("Steam Workshop", "activityCenter.sources.steamWorkshop"),
    "monitoring": ("Performance Monitor", "activityCenter.sources.performanceMonitor"),
    "task queue": ("Task Queue", "activityCenter.sources.taskQueue"),
}

_CATEGORY_KEYS = {
    "server": "activityCenter.categories.server",
    "application": "activityCenter.categories.application",
    "task": "activityCenter.categories.task",
}


def _task_level(status: str) -> str:
    if status == "failed":
        return "error"
    if status in {"cancelled", "cancelling"}:
        return "warning"
    return "info"


def _format_source(source: Any) -> tuple[str, str | None]:
    raw = str(source or "Exiles Game Manager").strip()
    label = _SOURCE_LABELS.get(raw.casefold())
    if label:
        return label
    if raw.startswith("egm."):
        component = raw.removeprefix("egm.").replace("_", " ").strip()
        pretty = " ".join(word.capitalize() for word in component.split()) or "EGM Service"
        return pretty, None
    return raw, None


def _format_message(source: str, message: Any) -> str:
    raw = str(message or "").strip()
    lowered = raw.casefold()
    if source == "EGM Update Service":
        if "404 not found" in lowered or "update check unavailable" in lowered:
            return "Update service not configured."
        if "currently unavailable" in lowered:
            return "Update server is currently unavailable."
    return raw


def _task_summary(task: dict[str, Any]) -> str:
    action = str(task.get("action") or "")
    error = str(task.get("error") or "").strip()
    if action.startswith("workshop."):
        if error:
            return "Steam Workshop update failed. " + error
        return "Steam Workshop task finished."
    if action.startswith("backup."):
        return "Backup task failed." if error else "Backup task finished."
    if action.startswith("firewall."):
        return "Firewall operation failed." if error else "Firewall operation finished."
    return error or str(task.get("message") or task.get("status") or "Task finished.")


def _strip_traceback(message: str) -> str:
    for marker in ("\nTraceback (most recent call last):", " Traceback (most recent call last):"):
        if marker in message:
            return message.split(marker, 1)[0].strip()
    return message.strip()


def _decorate(row: dict[str, Any], category: str, event_type: str) -> dict[str, Any]:
    source, source_key = _format_source(row.get("source"))
    result = {
        **row,
        "source": source,
        "message": _strip_traceback(_format_message(source, row.get("message"))),
        "category": category,
        "categoryKey": _CATEGORY_KEYS.get(category),
        "eventType": event_type,
    }
    if source_key:
        result["sourceKey"] = source_key
    return result


def list_events(
    *,
    instance_id: str | None,
    category: str | None,
    level: str | None,
    query: str | None,
    limit: int,
    mask_ips: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if category in {None, "all", "server"}:
        source_rows = activity_log.get_for_instance(instance_id) if instance_id else activity_log.get_all()
        rows.extend(_decorate(row, "server", "server.activity") for row in source_rows)

    if category in {None, "all", "application"}:
        rows.extend(
            _decorate(row, "application", "application.log")
            for row in app_event_log.get_all(limit=1000, mask_ips=mask_ips)
        )

    if category in {None, "all", "task"}:
        for task in task_queue.list_tasks(instance_id=instance_id, limit=1000):
            if task.get("status") not in {"completed", "failed", "cancelled"}:
                continue
            timestamp = task.get("finishedAt") or task.get("updatedAt") or task.get("createdAt")
            row = {
                "id": f"activity-{task['id']}",
                "timestamp": timestamp,
                "level": _task_level(str(task.get("status"))),
                "source": task.get("title") or task.get("action") or "Task Queue",
                "message": _task_summary(task),
                "technicalDetails": task.get("technicalDetails"),
                "instanceId": task.get("instanceId"),
                "taskId": task.get("id"),
                "status": task.get("status"),
                "progress": task.get("progress"),
            }
            rows.append(_decorate(row, "task", f"task.{task.get('status')}"))

    def epoch(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return 0.0
        return 0.0

    if level and level != "all":
        rows = [row for row in rows if row.get("level") == level]
    if query:
        needle = query.casefold()
        rows = [
            row
            for row in rows
            if needle
            in f"{row.get('source', '')} {row.get('message', '')} {row.get('eventType', '')}".casefold()
        ]
    rows.sort(key=lambda row: epoch(row.get("timestamp")), reverse=True)
    return rows[: max(1, min(limit, 1000))]

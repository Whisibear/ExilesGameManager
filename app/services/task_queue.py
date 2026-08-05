"""Persistent, multi-instance task queue for Exiles Game Manager.

Long-running or host-mutating operations are serialized per server instance.
Tasks survive frontend reloads, expose progress/logs, and are persisted under
EGM's data directory. Queued tasks are resumed after an application restart;
a task that was actively running during an unclean shutdown is marked failed
instead of being silently repeated.
"""
from __future__ import annotations

import asyncio
import copy
import json
import logging
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from app.paths import data_dir
from app.services import runtime_logging

logger = logging.getLogger("egm.task_queue")

TERMINAL_STATES = {"completed", "failed", "cancelled"}
ACTIVE_STATES = {"queued", "running", "paused", "cancelling"}
_MAX_LOG_LINES = 500
_TASK_FILE = "task_queue.json"


class TaskCancelled(Exception):
    pass


@dataclass
class TaskContext:
    task_id: str

    def _task(self) -> dict[str, Any]:
        task = _tasks.get(self.task_id)
        if task is None:
            raise TaskCancelled("Task no longer exists.")
        return task

    async def checkpoint(self) -> None:
        task = self._task()
        if task.get("cancelRequested"):
            raise TaskCancelled("Cancellation requested.")
        while task.get("pauseRequested"):
            task["status"] = "paused"
            task["updatedAt"] = _now()
            _persist()
            await asyncio.sleep(0.25)
            task = self._task()
            if task.get("cancelRequested"):
                raise TaskCancelled("Cancellation requested.")
        if task.get("status") == "paused":
            task["status"] = "running"
            task["updatedAt"] = _now()
            _persist()

    def log(self, message: str, level: str = "info") -> None:
        task = self._task()
        task.setdefault("log", []).append({"timestamp": _now(), "level": level, "message": str(message)})
        if len(task["log"]) > _MAX_LOG_LINES:
            task["log"] = task["log"][-_MAX_LOG_LINES:]
        task["updatedAt"] = _now()
        _persist()

    def progress(self, value: float, message: str | None = None) -> None:
        task = self._task()
        task["progress"] = max(0.0, min(100.0, float(value)))
        if message:
            task["message"] = message
        task["updatedAt"] = _now()
        _persist()


Handler = Callable[[TaskContext, dict[str, Any]], Awaitable[Any]]
_tasks: dict[str, dict[str, Any]] = {}
_queue: asyncio.PriorityQueue[tuple[int, float, str]] | None = None
_workers: list[asyncio.Task[None]] = []
_instance_locks: dict[str, asyncio.Lock] = {}
_waiters: dict[str, asyncio.Event] = {}
_started = False


def _path() -> Path:
    return data_dir() / _TASK_FILE


def _now() -> float:
    return time.time()


def _public(task: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(task)


def _persist() -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    payload = {"version": 1, "tasks": list(_tasks.values())}
    serialized = json.dumps(payload, indent=2, ensure_ascii=False)
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(path)

    # Keep a directly accessible, human-readable snapshot beside the installed
    # application so support logs never have to be searched for in ProgramData.
    try:
        visible = runtime_logging.logs_root() / "taskqueue" / "task_queue.json"
        visible_tmp = visible.with_suffix(".tmp")
        visible_tmp.write_text(serialized, encoding="utf-8")
        visible_tmp.replace(visible)
    except OSError:
        # Task persistence in ProgramData is authoritative; a support-log mirror
        # must never interrupt task execution.
        pass


def _load() -> None:
    _tasks.clear()
    path = _path()
    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for raw in payload.get("tasks", []):
            if not isinstance(raw, dict) or not raw.get("id"):
                continue
            task = dict(raw)
            if task.get("status") in {"running", "cancelling"}:
                task["status"] = "failed"
                task["error"] = "EGM stopped while this task was running. Retry it manually."
                task["finishedAt"] = _now()
                task["updatedAt"] = _now()
            _tasks[str(task["id"])] = task
    except Exception:
        logger.exception("Could not load persistent task queue")


def list_tasks(*, instance_id: str | None = None, status: str | None = None, limit: int = 250) -> list[dict[str, Any]]:
    rows = list(_tasks.values())
    if instance_id:
        rows = [row for row in rows if row.get("instanceId") == instance_id]
    if status:
        rows = [row for row in rows if row.get("status") == status]
    rows.sort(key=lambda row: (float(row.get("createdAt") or 0)), reverse=True)
    return [_public(row) for row in rows[: max(1, min(limit, 1000))]]


def get_task(task_id: str) -> dict[str, Any] | None:
    task = _tasks.get(task_id)
    return _public(task) if task else None


def _event(task_id: str) -> asyncio.Event:
    return _waiters.setdefault(task_id, asyncio.Event())


async def start() -> None:
    global _queue, _started
    if _started:
        return
    _load()
    _queue = asyncio.PriorityQueue()
    for task in _tasks.values():
        if task.get("status") == "queued":
            _queue.put_nowait((-int(task.get("priority") or 50), float(task.get("createdAt") or _now()), task["id"]))
    _workers.extend(asyncio.create_task(_worker(i), name=f"egm-task-worker-{i}") for i in range(3))
    _started = True
    _persist()
    logger.info("Task queue started with %d persisted task(s)", len(_tasks))


async def stop() -> None:
    for worker in list(_workers):
        worker.cancel()
    if _workers:
        await asyncio.gather(*_workers, return_exceptions=True)
    _workers.clear()


def enqueue(
    action: str,
    *,
    instance_id: str | None = None,
    payload: dict[str, Any] | None = None,
    title: str | None = None,
    priority: int = 50,
    created_by: str | None = None,
    max_retries: int = 0,
) -> dict[str, Any]:
    if not _started or _queue is None:
        raise RuntimeError("Task queue is not started.")
    task_id = f"task-{uuid.uuid4().hex}"
    now = _now()
    task = {
        "id": task_id,
        "action": action,
        "title": title or action,
        "instanceId": instance_id,
        "payload": payload or {},
        "status": "queued",
        "priority": max(0, min(100, int(priority))),
        "progress": 0.0,
        "message": "Queued",
        "log": [],
        "result": None,
        "error": None,
        "createdBy": created_by,
        "createdAt": now,
        "startedAt": None,
        "finishedAt": None,
        "updatedAt": now,
        "attempt": 0,
        "maxRetries": max(0, int(max_retries)),
        "cancelRequested": False,
        "pauseRequested": False,
        "etaSeconds": None,
    }
    _tasks[task_id] = task
    _event(task_id).clear()
    _queue.put_nowait((-task["priority"], task["createdAt"], task_id))
    _persist()
    return _public(task)


async def enqueue_and_wait(action: str, **kwargs: Any) -> Any:
    task = enqueue(action, **kwargs)
    await _event(task["id"]).wait()
    finished = _tasks[task["id"]]
    if finished["status"] == "completed":
        return copy.deepcopy(finished.get("result"))
    if finished["status"] == "cancelled":
        raise TaskCancelled(finished.get("error") or "Task cancelled.")
    raise RuntimeError(finished.get("error") or "Task failed.")


def create_external_task(action: str, *, title: str, message: str = "Running", priority: int = 50) -> str:
    """Create a visible task controlled by a service instead of a queue worker."""
    task_id = f"task-{uuid.uuid4().hex}"
    now = _now()
    _tasks[task_id] = {
        "id": task_id, "action": action, "title": title, "instanceId": None, "payload": {},
        "status": "running", "priority": max(0, min(100, int(priority))), "progress": 5.0,
        "message": message, "log": [{"timestamp": now, "level": "info", "message": message}],
        "result": None, "error": None, "technicalDetails": None, "createdBy": None,
        "createdAt": now, "startedAt": now, "finishedAt": None, "updatedAt": now,
        "attempt": 1, "maxRetries": 0, "cancelRequested": False, "pauseRequested": False,
        "etaSeconds": None,
    }
    _event(task_id).clear()
    _persist()
    return task_id


def update_external_task(task_id: str, *, message: str, progress: float | None = None, level: str = "info") -> None:
    task = _tasks.get(task_id)
    if not task or task.get("status") in TERMINAL_STATES:
        return
    task["message"] = message
    if progress is not None:
        task["progress"] = max(0.0, min(100.0, float(progress)))
    task.setdefault("log", []).append({"timestamp": _now(), "level": level, "message": message})
    task["updatedAt"] = _now()
    _persist()


def finish_external_task(task_id: str, *, success: bool, message: str, error: str | None = None) -> None:
    task = _tasks.get(task_id)
    if not task or task.get("status") in TERMINAL_STATES:
        return
    task["status"] = "completed" if success else "failed"
    task["progress"] = 100.0 if success else max(float(task.get("progress") or 0), 5.0)
    task["message"] = message
    task["error"] = None if success else (error or message)
    task["finishedAt"] = _now()
    task["updatedAt"] = _now()
    task.setdefault("log", []).append({"timestamp": _now(), "level": "info" if success else "error", "message": message})
    _persist()
    _publish_task_notification(task)
    _event(task_id).set()


def cancel(task_id: str) -> dict[str, Any]:
    task = _tasks.get(task_id)
    if not task:
        raise KeyError(task_id)
    if task["status"] in TERMINAL_STATES:
        return _public(task)
    task["cancelRequested"] = True
    task["pauseRequested"] = False
    if task["status"] in {"queued", "paused"}:
        task["status"] = "cancelled"
        task["error"] = "Cancelled by user."
        task["finishedAt"] = _now()
        _event(task_id).set()
    else:
        task["status"] = "cancelling"
        task["message"] = "Cancellation requested"
    task["updatedAt"] = _now()
    _persist()
    return _public(task)


def pause(task_id: str) -> dict[str, Any]:
    task = _tasks.get(task_id)
    if not task:
        raise KeyError(task_id)
    if task["status"] in TERMINAL_STATES:
        return _public(task)
    task["pauseRequested"] = True
    if task["status"] == "queued":
        task["status"] = "paused"
        task["message"] = "Paused"
    task["updatedAt"] = _now()
    _persist()
    return _public(task)


def resume(task_id: str) -> dict[str, Any]:
    task = _tasks.get(task_id)
    if not task:
        raise KeyError(task_id)
    if task["status"] in TERMINAL_STATES:
        return _public(task)
    task["pauseRequested"] = False
    if task["status"] == "paused" and task.get("startedAt") is None:
        task["status"] = "queued"
        task["message"] = "Queued"
        assert _queue is not None
        _queue.put_nowait((-int(task["priority"]), float(task["createdAt"]), task_id))
    task["updatedAt"] = _now()
    _persist()
    return _public(task)


def retry(task_id: str) -> dict[str, Any]:
    old = _tasks.get(task_id)
    if not old:
        raise KeyError(task_id)
    if old["status"] not in TERMINAL_STATES:
        raise ValueError("Only completed, failed, or cancelled tasks can be retried.")
    return enqueue(
        old["action"], instance_id=old.get("instanceId"), payload=copy.deepcopy(old.get("payload") or {}),
        title=old.get("title"), priority=int(old.get("priority") or 50), created_by=old.get("createdBy"),
        max_retries=int(old.get("maxRetries") or 0),
    )


def clear_completed() -> int:
    ids = [task_id for task_id, task in _tasks.items() if task.get("status") in TERMINAL_STATES]
    for task_id in ids:
        _tasks.pop(task_id, None)
        _waiters.pop(task_id, None)
    _persist()
    return len(ids)


async def _worker(index: int) -> None:
    assert _queue is not None
    while True:
        try:
            _priority, _created, task_id = await _queue.get()
            task = _tasks.get(task_id)
            if not task or task.get("status") != "queued":
                _queue.task_done()
                continue
            if task.get("pauseRequested"):
                task["status"] = "paused"
                _persist()
                _queue.task_done()
                continue
            lock_key = str(task.get("instanceId") or "__global__")
            lock = _instance_locks.setdefault(lock_key, asyncio.Lock())
            async with lock:
                await _execute(task_id)
            _queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Task worker %d failed", index)
            await asyncio.sleep(0.5)


async def _execute(task_id: str) -> None:
    task = _tasks[task_id]
    if task.get("cancelRequested"):
        cancel(task_id)
        return
    task["status"] = "running"
    task["startedAt"] = task.get("startedAt") or _now()
    task["updatedAt"] = _now()
    task["attempt"] = int(task.get("attempt") or 0) + 1
    task["message"] = "Running"
    _persist()
    ctx = TaskContext(task_id)
    ctx.log(f"Task started: {task['action']}")
    try:
        result = await _dispatch(ctx, task["action"], task.get("instanceId"), task.get("payload") or {})
        task["result"] = result
        task["status"] = "completed"
        task["progress"] = 100.0
        task["message"] = "Completed"
        task["finishedAt"] = _now()
        ctx.log("Task completed successfully.")
    except TaskCancelled as exc:
        task["status"] = "cancelled"
        task["error"] = str(exc)
        task["message"] = "Cancelled"
        task["finishedAt"] = _now()
        ctx.log(str(exc), "warning")
    except Exception as exc:
        logger.exception("Task %s (%s) failed", task_id, task["action"])
        task["error"] = str(exc)
        task["technicalDetails"] = getattr(exc, "technical_details", None) or traceback.format_exc()
        if int(task.get("attempt") or 0) <= int(task.get("maxRetries") or 0):
            task["status"] = "queued"
            task["message"] = "Retry queued"
            task["updatedAt"] = _now()
            ctx.log(f"Attempt failed; retry queued: {exc}", "warning")
            assert _queue is not None
            _queue.put_nowait((-int(task["priority"]), _now(), task_id))
            _persist()
            return
        task["status"] = "failed"
        task["message"] = "Failed"
        task["finishedAt"] = _now()
        ctx.log(f"Task failed: {exc}", "error")
    finally:
        task["updatedAt"] = _now()
        _persist()
        if task["status"] in TERMINAL_STATES:
            _publish_task_notification(task)
            _event(task_id).set()


def _publish_task_notification(task: dict[str, Any]) -> None:
    try:
        from app.services import notification_center
        status = str(task.get("status"))
        kind = "success" if status == "completed" else "warning" if status == "cancelled" else "error"
        notification_center.publish(
            kind, f"notifications.task.{status}.title", f"notifications.task.{status}.message",
            params={"title": task.get("title") or task.get("action"), "error": task.get("error") or ""},
            instance_id=task.get("instanceId"), category="task", audience="super_admin",
            fallback_title=f"Task {status}", fallback_message=str(task.get("error") or task.get("title") or task.get("action")),
            action_url=f"/tasks?task={task.get('id')}",
        )
    except Exception:
        logger.exception("Could not publish task notification")


async def _require_instance(instance_id: str | None) -> dict[str, Any]:
    from app.services import instance_store
    if not instance_id:
        raise ValueError("This task requires a server instance.")
    instance = instance_store.get(instance_id)
    if not instance:
        raise ValueError("Server instance not found.")
    return instance


async def _dispatch(ctx: TaskContext, action: str, instance_id: str | None, payload: dict[str, Any]) -> Any:
    await ctx.checkpoint()
    if action == "wishlist.record":
        event = str(payload.get("event") or "updated")
        source = str(payload.get("source") or "Mod")
        name = str(payload.get("name") or "Unknown mod")
        identity = str(payload.get("identity") or "").strip()
        ctx.progress(40, "Recording wishlist event")
        ctx.log(f"{source} wishlist request {event}: {name}{f' ({identity})' if identity else ''}.")
        ctx.progress(95, "Wishlist event recorded")
        return {"event": event, "source": source, "name": name, "identity": identity or None}
    if action == "backup.create":
        from app.services import backup_service
        instance = await _require_instance(instance_id)
        ctx.progress(10, "Preparing backup")
        ctx.log("Creating server backup.")
        result = await backup_service.run_backup(instance, kind=str(payload.get("kind") or "manual"))
        ctx.progress(95, "Finalizing backup")
        return result
    if action == "backup.verify":
        from app.services import backup_service
        await _require_instance(instance_id)
        ctx.progress(15, "Verifying backup")
        result = await asyncio.to_thread(backup_service.verify_backup, str(instance_id), str(payload["timestamp"]))
        ctx.progress(95, "Verification complete")
        return result
    if action == "backup.restore":
        from app.services import backup_service
        instance = await _require_instance(instance_id)
        ctx.progress(5, "Preparing restore")
        ctx.log("Restoring backup. The server may be stopped as required.")
        result = await backup_service.restore_backup(instance, str(payload["timestamp"]))
        ctx.progress(95, "Restore complete")
        return result
    if action == "firewall.sync_instance":
        from app.services import firewall
        instance = await _require_instance(instance_id)
        ctx.progress(20, "Checking firewall rules")
        result = await asyncio.to_thread(firewall.sync_instance, instance)
        ctx.progress(95, "Firewall synchronized")
        return result
    if action == "firewall.sync_all":
        from app.services import firewall, instance_store
        instances = instance_store.list_instances()
        created: list[str] = []
        existing: list[str] = []
        prompted = False
        for index, instance in enumerate(instances):
            await ctx.checkpoint()
            ctx.progress((index / max(1, len(instances))) * 90, f"Synchronizing {instance['name']}")
            row = await asyncio.to_thread(firewall.sync_instance, instance)
            created.extend(row.get("created", []))
            existing.extend(row.get("alreadyPresent", []))
            prompted = prompted or bool(row.get("uacPrompted"))
        return {"created": created, "alreadyPresent": existing, "uacPrompted": prompted}
    if action == "firewall.remove_instance":
        from app.services import firewall
        instance = await _require_instance(instance_id)
        ctx.progress(20, "Removing firewall rules")
        result = await asyncio.to_thread(firewall.delete_rules, [r.name for r in firewall.instance_rules(instance)])
        ctx.progress(95, "Firewall rules removed")
        return result
    if action == "mods.check_updates":
        from app.services import nexus_mod_service, steam_workshop
        instance = await _require_instance(instance_id)
        ctx.progress(5, "Checking Steam Workshop mods")
        ctx.log("Combined mod update check started for Steam Workshop and Nexus Mods.")
        steam = await steam_workshop.check_updates(instance)
        ctx.progress(50, "Checking Nexus Mods")
        nexus = await nexus_mod_service.check_updates(instance)
        total = int(steam.get("updatesAvailable") or 0) + int(nexus.get("updatesAvailable") or 0)
        checked = int(steam.get("checked") or 0) + int(nexus.get("checked") or 0)
        ctx.log(f"Combined check complete: {checked} checked, {total} update(s) available.")
        ctx.progress(100, "Mod update check complete")
        return {"checked": checked, "updatesAvailable": total, "upToDate": total == 0, "steam": steam, "nexus": nexus}
    if action == "mods.verify_startup":
        from app.services import mod_runtime_verifier
        instance = await _require_instance(instance_id)
        return await mod_runtime_verifier.verify_after_start(ctx, instance)
    if action in {"workshop.install", "workshop.update"}:
        from app.services import steam_workshop
        instance = await _require_instance(instance_id)
        wid = str(payload["workshopId"])
        ctx.progress(5, "Downloading Workshop item")
        ctx.log(f"Steam Workshop item {wid}: download and install started.")
        result = await steam_workshop.install(instance, wid, force_download=action == "workshop.update")
        ctx.progress(95, "Workshop mod configured")
        return result
    if action == "workshop.update_all":
        from app.services import steam_workshop
        instance = await _require_instance(instance_id)
        ctx.progress(5, "Creating compact safety backup")
        result = await steam_workshop.update_all(instance)
        ctx.progress(95, "Workshop mods updated")
        return result
    if action == "server.update":
        from app.services import server_update
        instance = await _require_instance(instance_id)
        return await server_update.run_update_operation(ctx, instance)
    if action == "nexus.install":
        from app.services import nexus_mod_service
        instance = await _require_instance(instance_id)
        ctx.progress(10, "Preparing Nexus Mods download")
        result = await nexus_mod_service.install_nexus_mod(instance, int(payload["nexusModId"]), payload.get("fileId"))
        ctx.progress(95, "Nexus mod installed")
        return result
    if action == "ue4ss.install":
        from app.services import ue4ss_installer
        instance = await _require_instance(instance_id)
        ctx.progress(10, "Downloading UE4SS")
        result = await ue4ss_installer.install(instance)
        ctx.progress(95, "UE4SS installed")
        return result
    raise ValueError(f"Unsupported task action: {action}")

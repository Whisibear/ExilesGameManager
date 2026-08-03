from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth_deps import get_current_user, require_super_admin
from app.services import task_queue

router = APIRouter()


class CreateTaskRequest(BaseModel):
    action: str = Field(min_length=1, max_length=100)
    instanceId: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    title: str | None = Field(default=None, max_length=200)
    priority: int = Field(default=50, ge=0, le=100)
    maxRetries: int = Field(default=0, ge=0, le=5)


_ALLOWED_ACTIONS = {
    "backup.create", "backup.verify", "backup.restore",
    "firewall.sync_instance", "firewall.sync_all", "firewall.remove_instance",
    "workshop.install", "workshop.update", "workshop.update_all",
    "server.update", "ue4ss.install", "nexus.install",
}


@router.get("")
async def list_tasks(instanceId: str | None = None, status: str | None = None, limit: int = 250):
    return {"tasks": task_queue.list_tasks(instance_id=instanceId, status=status, limit=limit)}


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@router.post("", dependencies=[Depends(require_super_admin)])
async def create_task(body: CreateTaskRequest, user=Depends(get_current_user)):
    if body.action not in _ALLOWED_ACTIONS:
        raise HTTPException(status_code=400, detail="Unsupported task action.")
    try:
        return task_queue.enqueue(
            body.action,
            instance_id=body.instanceId,
            payload=body.payload,
            title=body.title,
            priority=body.priority,
            created_by=user.get("username") if isinstance(user, dict) else None,
            max_retries=body.maxRetries,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _mutate(task_id: str, operation):
    try:
        return operation(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{task_id}/cancel", dependencies=[Depends(require_super_admin)])
async def cancel_task(task_id: str):
    return _mutate(task_id, task_queue.cancel)


@router.post("/{task_id}/pause", dependencies=[Depends(require_super_admin)])
async def pause_task(task_id: str):
    return _mutate(task_id, task_queue.pause)


@router.post("/{task_id}/resume", dependencies=[Depends(require_super_admin)])
async def resume_task(task_id: str):
    return _mutate(task_id, task_queue.resume)


@router.post("/{task_id}/retry", dependencies=[Depends(require_super_admin)])
async def retry_task(task_id: str):
    return _mutate(task_id, task_queue.retry)


@router.delete("/completed", dependencies=[Depends(require_super_admin)])
async def clear_completed():
    return {"deleted": task_queue.clear_completed()}

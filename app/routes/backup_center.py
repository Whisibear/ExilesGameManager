import asyncio
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from app.services import backup_service, instance_store, task_queue
from app.services.backup_service import BackupError

router = APIRouter()


def _instance(instance_id: str) -> dict[str, Any]:
    instance = instance_store.get(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Server instance not found.")
    return instance


@router.get("")
async def list_all_backups():
    rows = []
    for instance in instance_store.list_instances():
        backups = await asyncio.to_thread(backup_service.list_backups, instance["id"])
        total = sum(int(item.get("sizeBytes") or 0) for item in backups)
        rows.append({"instanceId": instance["id"], "instanceName": instance["name"], "totalBytes": total, "backups": backups})
    return {"servers": rows}


@router.post("/{instance_id}/run")
async def run_backup(instance_id: str):
    instance = _instance(instance_id)
    try:
        return await task_queue.enqueue_and_wait("backup.create", instance_id=instance_id, title="Create backup")
    except (BackupError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{instance_id}/{timestamp}/verify")
async def verify(instance_id: str, timestamp: str):
    _instance(instance_id)
    try:
        return await task_queue.enqueue_and_wait("backup.verify", instance_id=instance_id, payload={"timestamp": timestamp}, title="Verify backup")
    except (BackupError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=getattr(exc, "message", str(exc))) from exc


@router.post("/{instance_id}/{timestamp}/restore")
async def restore(instance_id: str, timestamp: str):
    instance = _instance(instance_id)
    try:
        return await task_queue.enqueue_and_wait("backup.restore", instance_id=instance_id, payload={"timestamp": timestamp}, title="Restore backup")
    except (BackupError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=getattr(exc, "message", str(exc))) from exc


@router.delete("/{instance_id}/{timestamp}")
async def delete(instance_id: str, timestamp: str):
    _instance(instance_id)
    target = instance_store.instance_dir(instance_id) / "backups" / timestamp
    if not target.is_dir():
        raise HTTPException(status_code=404, detail="Backup not found.")
    await asyncio.to_thread(shutil.rmtree, target)
    return {"deleted": True}


@router.get("/{instance_id}/{timestamp}/export")
async def export(instance_id: str, timestamp: str, background_tasks: BackgroundTasks):
    instance = _instance(instance_id)
    try:
        zip_path = await asyncio.to_thread(backup_service.export_backup_zip, instance_id, timestamp)
    except (BackupError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=getattr(exc, "message", str(exc))) from exc
    background_tasks.add_task(zip_path.unlink, missing_ok=True)
    return FileResponse(zip_path, filename=f"{instance['name']}-{timestamp}.zip", media_type="application/zip")

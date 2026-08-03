"""SteamCMD-backed update checks integrated with the EGM task queue."""
import asyncio
import logging
from pathlib import Path
from typing import Any

from app.services import steamcmd, task_queue

logger = logging.getLogger("egm.server_update")


async def check_for_update(instance: dict[str, Any]) -> dict[str, Any]:
    install_dir = Path(instance["serverPath"])
    installed = await asyncio.to_thread(steamcmd.installed_build_id, install_dir)
    latest = await steamcmd.latest_public_build_id()
    return {
        "installedBuildId": installed,
        "latestBuildId": latest,
        "updateAvailable": bool(installed and latest and installed != latest),
        "canCompare": bool(installed and latest),
    }


async def run_update_operation(ctx: task_queue.TaskContext, instance: dict[str, Any]) -> dict[str, Any]:
    ctx.progress(5, "Checking Steam build IDs")
    ctx.log("Checking installed and latest Steam build IDs.")
    before = await check_for_update(instance)
    await ctx.checkpoint()
    ctx.progress(15, "Running SteamCMD update")

    def on_output(line: str) -> None:
        ctx.log(line, "debug")

    await steamcmd.install_palserver(Path(instance["serverPath"]), on_output=on_output)
    await ctx.checkpoint()
    ctx.progress(90, "Validating updated build")
    after = await check_for_update(instance)
    return {
        "installedBuildId": after["installedBuildId"],
        "latestBuildId": after["latestBuildId"],
        "before": before,
        "after": after,
    }


def start_update(instance: dict[str, Any]) -> str:
    task = task_queue.enqueue(
        "server.update",
        instance_id=instance["id"],
        title=f"Update {instance.get('name', 'server')}",
        priority=70,
    )
    return task["id"]


def get_job(job_id: str) -> dict[str, Any] | None:
    task = task_queue.get_task(job_id)
    if not task:
        return None
    result = task.get("result") or {}
    status_map = {
        "queued": "running", "paused": "running", "running": "running", "cancelling": "running",
        "completed": "done", "failed": "error", "cancelled": "error",
    }
    return {
        "status": status_map.get(task.get("status"), "running"),
        "log": [entry.get("message", "") for entry in task.get("log", [])],
        "error": task.get("error"),
        "installedBuildId": result.get("installedBuildId"),
        "latestBuildId": result.get("latestBuildId"),
        "taskId": task["id"],
        "progress": task.get("progress", 0),
    }

import asyncio
import logging
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.games.providers import (
    ProviderUnavailableError,
    get_provider_for_instance,
)
from app.games.providers.base import ServerControlProvider
from app.services import (
    activity_log,
    conan_live_console,
    conan_rcon,
    instance_store,
    mods_store,
    process_manager,
    task_queue,
)
from app.services.palworld_rest import PalworldRestError
from app.services.conan_rcon import ConanRconError
from app.services.process_manager import ProcessError
from app.services.steamcmd import SteamCmdError

logger = logging.getLogger("egm.server_control")

router = APIRouter()

# Countdown timers are implemented as our own cancellable asyncio tasks so the
# app can still cancel before the final shutdown call is sent.
_countdown_tasks: dict[str, asyncio.Task] = {}

_OFFLINE_STATUS: dict[str, Any] = {
    "state": "offline",
    "map": "",
    "uptimeSeconds": 0,
    "cpuPercent": 0,
    "ramUsedGB": 0,
    "ramTotalGB": 0,
    "systemCpuPercent": 0,
    "systemRamUsedGB": 0,
    "tickRateMs": None,
    "targetTickRateMs": 0,
    "playersOnline": 0,
    "maxPlayers": 0,
    "serverVersion": "",
    "modCount": 0,
    "lastSavedAt": "",
}


def _system_load() -> dict[str, Any]:
    """Whole-machine load, independent of Palworld - lets the Dashboard show
    "is Palworld itself struggling" and "is this machine under heavy load
    from something else" as two separate numbers instead of one conflated
    one. cpu_percent(interval=None) is the correct non-blocking usage here:
    it reports the delta since the last call, which is exactly what a
    polling loop like this one wants."""
    return {
        "systemCpuPercent": round(psutil.cpu_percent(interval=None), 1),
        "systemRamUsedGB": round(psutil.virtual_memory().used / (1024**3), 2),
    }


def _require_active_instance() -> dict[str, Any]:
    instance = instance_store.get_active()
    if not instance:
        raise HTTPException(status_code=400, detail="No server selected. Create or import one in Settings.")
    return instance


def _control_provider(
    instance: dict[str, Any],
) -> ServerControlProvider:
    try:
        return get_provider_for_instance(instance).control
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _status_view(
    instance: dict[str, Any] | None,
    provider: ServerControlProvider | None = None,
) -> dict[str, Any]:
    if not instance:
        return {**_OFFLINE_STATUS, **_system_load()}

    resolved = provider or _control_provider(instance)
    stats = process_manager.get_status(instance["id"])
    max_players = resolved.read_max_players(instance)
    mod_count = len(mods_store.load_mods(instance["id"]))
    game = instance_store.get_game_definition(instance)

    return {
        **_OFFLINE_STATUS,
        **_system_load(),
        "state": stats["state"],
        "uptimeSeconds": stats["uptimeSeconds"],
        "cpuPercent": stats["cpuPercent"],
        "ramUsedGB": stats["ramUsedGB"],
        "ramTotalGB": round(psutil.virtual_memory().total / (1024**3), 1),
        "maxPlayers": max_players,
        "modCount": mod_count,
        "lastSavedAt": process_manager.get_last_saved(instance["id"]) or "",
        "gameId": game.id,
        "gameEdition": game.edition,
        "providerId": resolved.game_id,
        "capabilities": game.capabilities.to_dict(),
    }


async def _status_view_async(
    instance: dict[str, Any] | None,
) -> dict[str, Any]:
    if not instance:
        return await asyncio.to_thread(_status_view, None)
    provider = _control_provider(instance)
    view = await asyncio.to_thread(_status_view, instance, provider)
    return await provider.enrich_status(instance, view)


@router.get("/status")
async def get_status() -> dict[str, Any]:
    instance = instance_store.get_active()
    return await _status_view_async(instance)


@router.post("/start")
async def start_server() -> dict[str, Any]:
    instance = _require_active_instance()
    activity_log.log("info", instance["name"], "Manual server start requested.")
    provider = _control_provider(instance)
    try:
        await provider.start(instance)
    except ProcessError as e:
        raise HTTPException(status_code=400, detail=e.message)
    game = instance_store.get_game_definition(instance)
    if game.family == "palworld":
        task_queue.enqueue(
            "mods.verify_startup",
            instance_id=instance["id"],
            title="Verify mods after server start",
        )
        activity_log.log("info", instance["name"], "Palworld mod startup verification queued in Task Queue.", instance_id=instance["id"])
    return await _status_view_async(instance)


@router.post("/stop")
async def stop_server() -> dict[str, Any]:
    instance = _require_active_instance()
    activity_log.log("info", instance["name"], "Manual server stop requested.")
    provider = _control_provider(instance)
    await provider.stop(instance)
    return await _status_view_async(instance)


@router.post("/restart")
async def restart_server() -> dict[str, Any]:
    instance = _require_active_instance()
    activity_log.log("info", instance["name"], "Manual server restart requested.")
    provider = _control_provider(instance)
    try:
        await provider.restart(instance)
    except ProcessError as e:
        raise HTTPException(status_code=400, detail=e.message)
    game = instance_store.get_game_definition(instance)
    if game.family == "palworld":
        task_queue.enqueue(
            "mods.verify_startup",
            instance_id=instance["id"],
            title="Verify mods after server start",
        )
        activity_log.log("info", instance["name"], "Palworld mod startup verification queued in Task Queue.", instance_id=instance["id"])
    return await _status_view_async(instance)


@router.post("/save")
async def save_world() -> dict[str, Any]:
    instance = _require_active_instance()
    activity_log.log("info", instance["name"], "Manual world save requested.")
    provider = _control_provider(instance)
    try:
        saved_at = await provider.save(instance)
    except PalworldRestError as e:
        raise HTTPException(status_code=400, detail=e.message)
    activity_log.log("info", instance["name"], "World save completed successfully.")
    return {"savedAt": saved_at}


@router.get("/update/check")
async def check_update() -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _control_provider(instance)
    try:
        return await provider.check_update(instance)
    except SteamCmdError as e:
        raise HTTPException(status_code=502, detail=e.message)


@router.post("/update/start")
async def start_update() -> dict[str, Any]:
    instance = _require_active_instance()
    status = process_manager.get_status(instance["id"])
    if status["state"] != "offline":
        raise HTTPException(status_code=400, detail="Stop this server before updating its files.")
    provider = _control_provider(instance)
    return {"jobId": provider.start_update(instance)}


@router.get("/update/{job_id}")
async def get_update_status(job_id: str) -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _control_provider(instance)
    job = provider.get_update_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="No such update job.")
    return job


class BroadcastRequest(BaseModel):
    message: str


@router.post("/broadcast")
async def broadcast_message(body: BroadcastRequest) -> dict[str, Any]:
    instance = _require_active_instance()
    activity_log.log("info", instance["name"], "Broadcast message requested by an administrator.")
    provider = _control_provider(instance)
    try:
        await provider.broadcast(instance, body.message)
    except (PalworldRestError, ConanRconError) as e:
        activity_log.log(
            "error",
            instance["name"],
            f"Broadcast message failed: {e.message}",
            instance_id=instance["id"],
        )
        raise HTTPException(status_code=400, detail=e.message)
    activity_log.log(
        "info",
        instance["name"],
        "Broadcast message sent successfully.",
        instance_id=instance["id"],
    )
    return {"message": body.message}


class RconCommandRequest(BaseModel):
    command: str


@router.get("/rcon/status")
async def get_rcon_status() -> dict[str, Any]:
    instance = _require_active_instance()
    game = instance_store.get_game_definition(instance)
    if not game.capabilities.rcon:
        raise HTTPException(
            status_code=409,
            detail=f"{game.label} does not expose RCON.",
        )
    try:
        return await conan_rcon.check_ready(instance)
    except ConanRconError as exc:
        return {
            "ready": False,
            "host": "127.0.0.1",
            "port": int((instance.get("ports") or {}).get("rcon") or instance.get("rconPort") or 25575),
            "error": exc.message,
        }


@router.post("/rcon")
async def execute_rcon_command(body: RconCommandRequest) -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _control_provider(instance)
    game = instance_store.get_game_definition(instance)
    if not game.capabilities.rcon:
        raise HTTPException(
            status_code=409,
            detail=f"{game.label} does not expose an RCON console.",
        )
    if provider.game_id != instance.get("gameId"):
        raise HTTPException(status_code=409, detail="Active provider mismatch.")
    command = conan_rcon.sanitize_command_for_log(body.command)
    try:
        response = await conan_rcon.execute(instance, body.command)
    except ConanRconError as exc:
        activity_log.log(
            "error",
            instance["name"],
            f"Conan RCON command failed: {command}. {exc.message}",
            instance_id=instance["id"],
        )
        raise HTTPException(status_code=400, detail=exc.message) from exc
    activity_log.log(
        "info",
        instance["name"],
        f"Conan RCON command executed: {command}.",
        instance_id=instance["id"],
    )
    endpoint = conan_rcon.endpoint_for(instance)
    return {"response": response, "command": command, "endpoint": f"{endpoint.host}:{endpoint.port}"}


@router.get("/live-console")
async def get_live_console(cursor: int | None = None) -> dict[str, Any]:
    instance = _require_active_instance()
    provider = _control_provider(instance)
    game = instance_store.get_game_definition(instance)
    if not game.capabilities.live_console:
        raise HTTPException(
            status_code=409,
            detail=f"{game.label} does not expose a live server console.",
        )
    if provider.game_id != instance.get("gameId"):
        raise HTTPException(status_code=409, detail="Active provider mismatch.")
    return await asyncio.to_thread(
        conan_live_console.read_chunk,
        instance,
        cursor,
    )


async def _try_broadcast(
    instance: dict[str, Any],
    provider: ServerControlProvider,
    message: str,
) -> None:
    try:
        await provider.broadcast(instance, message)
    except (PalworldRestError, ConanRconError) as e:
        logger.info("shutdown countdown: broadcast skipped for %s (%s)", instance["name"], e.message)


async def _run_countdown(
    instance: dict[str, Any],
    provider: ServerControlProvider,
    seconds: int,
) -> None:
    try:
        await _try_broadcast(
            instance,
            provider,
            f"The realm will fall silent in {seconds} seconds.",
        )
        if seconds > 10:
            await asyncio.sleep(seconds - 10)
            await _try_broadcast(
                instance,
                provider,
                "The realm will fall silent in 10 seconds.",
            )
            await asyncio.sleep(10)
        else:
            await asyncio.sleep(seconds)
        await _try_broadcast(
            instance,
            provider,
            "The realm falls silent now.",
        )
        await provider.shutdown(instance, "Server shutting down.")
    except asyncio.CancelledError:
        await _try_broadcast(
            instance,
            provider,
            "The scheduled shutdown was cancelled.",
        )
        raise
    finally:
        _countdown_tasks.pop(instance["id"], None)


class ShutdownCountdownRequest(BaseModel):
    seconds: int


@router.post("/shutdown-countdown")
async def start_shutdown_countdown(body: ShutdownCountdownRequest) -> dict[str, Any]:
    instance = _require_active_instance()
    if body.seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be positive.")
    existing = _countdown_tasks.get(instance["id"])
    if existing and not existing.done():
        raise HTTPException(status_code=400, detail="A shutdown countdown is already running for this server.")
    provider = _control_provider(instance)
    _countdown_tasks[instance["id"]] = asyncio.create_task(
        _run_countdown(instance, provider, body.seconds)
    )
    return {"seconds": body.seconds}


@router.post("/cancel-shutdown-countdown")
async def cancel_shutdown_countdown() -> dict[str, Any]:
    instance = _require_active_instance()
    task = _countdown_tasks.get(instance["id"])
    if task and not task.done():
        task.cancel()
        return {"cancelled": True}
    return {"cancelled": False}

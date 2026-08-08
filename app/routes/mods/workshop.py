from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth_deps import require_super_admin
from app.routes.mods._shared import require_active_instance
from app.services import conan_workshop, instance_store, steam_workshop, task_queue

router = APIRouter()


class WorkshopRequest(BaseModel):
    workshopId: str = Field(min_length=1, max_length=256)




@router.post("/workshop/details")
async def workshop_details(body: WorkshopRequest) -> dict[str, Any]:
    instance = require_active_instance()
    game = instance_store.get_game_definition(instance)
    try:
        if game.family == "conan_exiles":
            return await conan_workshop.get_details(instance, body.workshopId)
        return await steam_workshop.get_details(body.workshopId)
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc


@router.post("/workshop/install", dependencies=[Depends(require_super_admin)])
async def install_workshop(body: WorkshopRequest) -> list[dict[str, Any]]:
    instance = require_active_instance()
    try:
        return await task_queue.enqueue_and_wait("workshop.install", instance_id=instance["id"], payload={"workshopId": body.workshopId}, title="Install Steam Workshop mod")
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Workshop installation failed: {exc}") from exc



@router.post("/workshop/steamcmd-console/open", dependencies=[Depends(require_super_admin)])
async def open_steamcmd_console() -> dict[str, object]:
    try:
        return await steam_workshop.steamcmd.open_interactive_console()
    except steam_workshop.steamcmd.SteamCmdError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc



@router.get("/workshop/cache", dependencies=[Depends(require_super_admin)])
async def scan_workshop_cache() -> list[dict[str, Any]]:
    instance = require_active_instance()
    game = instance_store.get_game_definition(instance)
    if game.family == "conan_exiles":
        return await conan_workshop.scan_downloaded_cache(instance)
    return await steam_workshop.scan_downloaded_cache(instance)


@router.post("/workshop/cache/{workshop_id}/install", dependencies=[Depends(require_super_admin)])
async def install_workshop_from_cache(workshop_id: str) -> list[dict[str, Any]]:
    instance = require_active_instance()
    try:
        game = instance_store.get_game_definition(instance)
        cached = await (conan_workshop.scan_downloaded_cache(instance) if game.family == "conan_exiles" else steam_workshop.scan_downloaded_cache(instance))
        item = next((entry for entry in cached if entry["workshopId"] == workshop_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Workshop item was not found in the SteamCMD cache.")
        if not item.get("valid"):
            raise HTTPException(status_code=422, detail=item.get("validationError") or "The cached Workshop item is invalid.")
        return await task_queue.enqueue_and_wait(
            "workshop.install",
            instance_id=instance["id"],
            payload={"workshopId": workshop_id},
            title="Install downloaded Steam Workshop mod",
        )
    except HTTPException:
        raise
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc

@router.get("/check-all-updates", dependencies=[Depends(require_super_admin)])
async def check_all_mod_updates() -> dict[str, Any]:
    instance = require_active_instance()
    try:
        return await task_queue.enqueue_and_wait(
            "mods.check_updates",
            instance_id=instance["id"],
            title="Check Steam and Nexus mod updates",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workshop/check-updates", dependencies=[Depends(require_super_admin)])
async def check_workshop_updates() -> dict[str, Any]:
    instance = require_active_instance()
    game = instance_store.get_game_definition(instance)
    try:
        if game.family == "conan_exiles":
            return await conan_workshop.check_updates(instance)
        return await steam_workshop.check_updates(instance)
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc


@router.post("/workshop/{workshop_id}/update", dependencies=[Depends(require_super_admin)])
async def update_workshop(workshop_id: str) -> list[dict[str, Any]]:
    instance = require_active_instance()
    try:
        return await task_queue.enqueue_and_wait("workshop.update", instance_id=instance["id"], payload={"workshopId": workshop_id}, title="Update Steam Workshop mod")
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc


@router.post("/workshop/update-all", dependencies=[Depends(require_super_admin)])
async def update_all_workshop() -> dict[str, Any]:
    instance = require_active_instance()
    try:
        return await task_queue.enqueue_and_wait("workshop.update_all", instance_id=instance["id"], title="Update all Steam Workshop mods")
    except (steam_workshop.WorkshopError, RuntimeError) as exc:
        raise HTTPException(status_code=getattr(exc, "status_code", 500), detail=getattr(exc, "message", str(exc))) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Workshop update backup or installation failed: {exc}") from exc







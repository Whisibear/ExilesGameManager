from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.auth_deps import get_current_user, require_super_admin
from app.routes.mods._shared import require_active_instance
from app.services import activity_log, mod_wishlist, nexus_client, nexus_mod_service, steam_workshop, task_queue

router = APIRouter()


class WishlistRequest(BaseModel):
    source: Literal["nexus", "steam"] = "nexus"
    nexusModId: int | None = Field(default=None, gt=0)
    workshopId: str | None = Field(default=None, min_length=6, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    summary: str = Field(default="", max_length=2000)
    pictureUrl: str | None = Field(default=None, max_length=2000)

    @field_validator("workshopId", mode="before")
    @classmethod
    def normalize_workshop_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text[:200] or "Unnamed mod"

    @field_validator("author", mode="before")
    @classmethod
    def normalize_author(cls, value: Any) -> str:
        text = str(value or "").strip()
        return text[:100] or "Unknown author"

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: Any) -> str:
        return str(value or "").strip()[:2000]

    @field_validator("pictureUrl", mode="before")
    @classmethod
    def normalize_picture_url(cls, value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text[:2000] or None


@router.get("/wishlist")
async def get_wishlist() -> list[dict[str, Any]]:
    instance = require_active_instance()
    return mod_wishlist.list_requests(instance["id"])


@router.post("/wishlist")
async def add_to_wishlist(body: WishlistRequest, user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    instance = require_active_instance()
    data = body.model_dump()
    if body.source == "steam":
        if not body.workshopId:
            raise HTTPException(status_code=422, detail="workshopId is required for Steam Workshop wishlist items.")
        data["workshopId"] = steam_workshop.parse_workshop_id(body.workshopId)
        data["steamUrl"] = f"https://steamcommunity.com/sharedfiles/filedetails/?id={data['workshopId']}"
    else:
        if not body.nexusModId:
            raise HTTPException(status_code=422, detail="nexusModId is required for Nexus wishlist items.")
        data["nexusUrl"] = f"https://www.nexusmods.com/{nexus_client.GAME_DOMAIN}/mods/{body.nexusModId}"
    updated = mod_wishlist.add_request(instance["id"], data, user)
    source_label = "Steam Workshop" if body.source == "steam" else "Nexus Mods"
    identity = data.get("workshopId") if body.source == "steam" else data.get("nexusModId")
    await task_queue.enqueue_and_wait(
        "wishlist.record",
        instance_id=instance["id"],
        payload={"event": "added", "source": source_label, "name": body.name, "identity": str(identity)},
        title=f"Add {source_label} request to wishlist",
        created_by=user.get("username"),
    )
    activity_log.log(
        "info", instance.get("name") or "Mod Wishlist",
        f"{source_label} request added to the mod wishlist: {body.name} ({identity}) by {user.get('username') or 'administrator'}.",
        instance_id=instance["id"],
    )
    return updated


@router.post("/wishlist/{request_id}/approve", dependencies=[Depends(require_super_admin)])
async def approve_wishlist_request(request_id: str) -> list[dict[str, Any]]:
    instance = require_active_instance()
    request = mod_wishlist.get_request(instance["id"], request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Mod wishlist request not found.")
    if request.get("source") == "steam":
        workshop_id = str(request["workshopId"])
        cached = await steam_workshop.scan_downloaded_cache(instance)
        item = next((entry for entry in cached if str(entry.get("workshopId")) == workshop_id), None)
        if not item:
            activity_log.log("warning", instance.get("name") or "Mod Wishlist", f"Steam Workshop wishlist approval is waiting for cache download: {request.get('name')} ({workshop_id}).", instance_id=instance["id"])
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Workshop item {workshop_id} is not downloaded yet. Open SteamCMD Console in "
                    "Super Admin, download it with 'workshop_download_item 1623730 "
                    f"{workshop_id} validate', then approve this request again."
                ),
            )
        if not item.get("valid"):
            raise HTTPException(
                status_code=422,
                detail=item.get("validationError") or "The downloaded Workshop item is invalid.",
            )
        await task_queue.enqueue_and_wait(
            "workshop.install",
            instance_id=instance["id"],
            payload={"workshopId": workshop_id},
            title="Install downloaded Steam Workshop mod",
        )
    else:
        await nexus_mod_service.install_nexus_mod(instance, int(request["nexusModId"]))
    mod_wishlist.remove_request(instance["id"], request_id)
    source_label = "Steam Workshop" if request.get("source") == "steam" else "Nexus Mods"
    activity_log.log(
        "info", instance.get("name") or "Mod Wishlist",
        f"{source_label} wishlist request approved and installed: {request.get('name') }.",
        instance_id=instance["id"],
    )
    return mod_wishlist.list_requests(instance["id"])


@router.post("/wishlist/{request_id}/deny", dependencies=[Depends(require_super_admin)])
async def deny_wishlist_request(request_id: str, user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    instance = require_active_instance()
    request = mod_wishlist.get_request(instance["id"], request_id)
    if not request or not mod_wishlist.remove_request(instance["id"], request_id):
        raise HTTPException(status_code=404, detail="Mod wishlist request not found.")
    source_label = "Steam Workshop" if request.get("source") == "steam" else "Nexus Mods"
    await task_queue.enqueue_and_wait(
        "wishlist.record",
        instance_id=instance["id"],
        payload={"event": "denied", "source": source_label, "name": request.get("name", "Unknown mod")},
        title=f"Deny {source_label} wishlist request",
        created_by=user.get("username"),
    )
    activity_log.log(
        "warning", instance.get("name") or "Mod Wishlist",
        f"{source_label} wishlist request denied: {request.get('name')} by {user.get('username') or 'administrator'}.",
        instance_id=instance["id"],
    )
    return mod_wishlist.list_requests(instance["id"])

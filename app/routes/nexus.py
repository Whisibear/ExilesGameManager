from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth_deps import require_super_admin
from app.services import nexus_client, nexus_oauth, nexus_session
from app.services.nexus_client import NexusApiError

router = APIRouter()


# account_view() exposes only non-sensitive Nexus account metadata. OAuth tokens
# remain encrypted in the local secure store and are never returned to the frontend.
@router.get("/account")
async def get_account() -> dict[str, Any]:
    return nexus_session.account_view()


@router.post("/oauth/start", dependencies=[Depends(require_super_admin)])
async def start_oauth() -> dict[str, Any]:
    return nexus_oauth.start()


@router.get("/oauth/status/{request_id}", dependencies=[Depends(require_super_admin)])
async def get_oauth_status(request_id: str) -> dict[str, Any]:
    status = nexus_oauth.get_status(request_id)
    if not status:
        raise HTTPException(status_code=404, detail="This Nexus Mods authorization request expired. Try again.")
    return status


@router.post("/disconnect", dependencies=[Depends(require_super_admin)])
async def disconnect() -> dict[str, Any]:
    nexus_session.disconnect()
    return {"connected": False}


def _map_mod_summary(m: dict[str, Any]) -> dict[str, Any]:
    mod_id = m.get("modId")
    category = m.get("category") or "Uncategorized"
    return {
        "id": str(mod_id),
        "modId": mod_id,
        "name": m.get("name") or "Untitled Mod",
        "author": m.get("author") or "Unknown",
        "summary": m.get("summary") or "",
        "version": "See Nexus",
        "categoryId": None,
        "categoryName": category,
        "downloads": m.get("downloads") or 0,
        "endorsements": m.get("endorsements") or 0,
        "pictureUrl": m.get("pictureUrl"),
        "directDownloadEnabled": bool(m.get("directDownloadEnabled")),
        "nexusUrl": f"https://www.nexusmods.com/{nexus_client.GAME_DOMAIN}/mods/{mod_id}",
    }


@router.get("/mods")
async def list_mods(
    list: str = Query("trending", pattern="^(trending|latest_added|latest_updated)$"),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    try:
        page = await nexus_client.get_mod_list(list, offset)
    except NexusApiError as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    return {"results": [_map_mod_summary(m) for m in page["nodes"]], "totalCount": page["totalCount"]}


@router.get("/search")
async def search_mods(q: str = Query(min_length=1, max_length=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    """Real Nexus-side search by name (TICKET-0144), not just a client-side
    filter over whichever 60 mods the trending/latest lists already loaded.
    Paginated (TICKET-0149) - a broad search can easily match more than one
    page's worth, and previously results past the first (hardcoded) 60 were
    simply unreachable."""
    try:
        page = await nexus_client.search_mods(q, offset)
    except NexusApiError as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    return {"results": [_map_mod_summary(m) for m in page["nodes"]], "totalCount": page["totalCount"]}

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services import steam_workshop, steam_workshop_browser

router = APIRouter()


@router.get("/mods")
async def list_mods(
    list: str = Query("trending", pattern="^(trending|latest_added|latest_updated)$"),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    try:
        return await steam_workshop_browser.browse(list, offset)
    except steam_workshop.WorkshopError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/search")
async def search_mods(q: str = Query(min_length=1, max_length=200), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    try:
        return await steam_workshop_browser.search(q, offset)
    except steam_workshop.WorkshopError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

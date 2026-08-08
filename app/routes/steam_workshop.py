from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services import conan_workshop, instance_store, steam_workshop, steam_workshop_browser

router = APIRouter()

def _browser_context(catalog: str | None = None):
    instance = instance_store.get_active()
    normalized = (catalog or "").strip().lower()
    if normalized == "conan":
        if not instance:
            raise steam_workshop.WorkshopError("Select a Conan Exiles server before browsing its Workshop.", 409)
        game = instance_store.get_game_definition(instance)
        if game.family != "conan_exiles":
            raise steam_workshop.WorkshopError("The active server is not a Conan Exiles server.", 409)
        async def conan_loader(ids):
            return await conan_workshop.get_details_many(instance, ids)
        return conan_workshop.CONAN_WORKSHOP_APP_ID, conan_loader
    if normalized == "palworld":
        return steam_workshop.PALWORLD_APP_ID, steam_workshop.get_details_many
    if not instance:
        return steam_workshop.PALWORLD_APP_ID, steam_workshop.get_details_many
    game = instance_store.get_game_definition(instance)
    if game.family == "conan_exiles":
        async def conan_loader(ids):
            return await conan_workshop.get_details_many(instance, ids)
        return conan_workshop.CONAN_WORKSHOP_APP_ID, conan_loader
    return steam_workshop.PALWORLD_APP_ID, steam_workshop.get_details_many



@router.get("/mods")
async def list_mods(
    list: str = Query("trending", pattern="^(trending|latest_added|latest_updated)$"),
    offset: int = Query(0, ge=0),
    catalog: str | None = Query(None, pattern="^(conan|palworld)$"),
) -> dict[str, Any]:
    try:
        app_id, loader = _browser_context(catalog)
        return await steam_workshop_browser.browse(list, offset, app_id=app_id, details_loader=loader)
    except steam_workshop.WorkshopError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/search")
async def search_mods(
    q: str = Query(min_length=1, max_length=200),
    offset: int = Query(0, ge=0),
    catalog: str | None = Query(None, pattern="^(conan|palworld)$"),
) -> dict[str, Any]:
    try:
        app_id, loader = _browser_context(catalog)
        return await steam_workshop_browser.search(q, offset, app_id=app_id, details_loader=loader)
    except steam_workshop.WorkshopError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

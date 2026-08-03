import html
import logging
import re
from typing import Any

import httpx

from app.services import steam_workshop

logger = logging.getLogger("egm.steam_workshop_browser")
APP_ID = steam_workshop.PALWORLD_APP_ID
BROWSE_URL = "https://steamcommunity.com/workshop/browse/"
PAGE_SIZE = 30
_ITEM_RE = re.compile(r"sharedfiles/filedetails/\?id=(\d{6,20})")
_TOTAL_RE = re.compile(r"Showing\s+\d+-\d+\s+of\s+([\d,\.]+)", re.I)

_SORTS = {
    "trending": "trend",
    "latest_added": "mostrecent",
    "latest_updated": "lastupdated",
}


def _extract_ids(page_html: str) -> list[str]:
    found: list[str] = []
    for item_id in _ITEM_RE.findall(page_html):
        if item_id not in found:
            found.append(item_id)
    return found


def _extract_total(page_html: str, fallback: int) -> int:
    match = _TOTAL_RE.search(html.unescape(page_html))
    if not match:
        return fallback
    digits = re.sub(r"\D", "", match.group(1))
    return int(digits) if digits else fallback


def _map_item(item: dict[str, Any]) -> dict[str, Any]:
    tags = item.get("tags") or []
    category = next((str(tag.get("tag")) for tag in tags if tag.get("tag")), "Workshop")
    return {
        "id": str(item["workshopId"]),
        "workshopId": str(item["workshopId"]),
        "name": item.get("title") or f"Workshop {item['workshopId']}",
        "author": item.get("owner") or "Steam Workshop",
        "summary": item.get("description") or "",
        "categoryName": category,
        "subscriptions": int(item.get("subscriptions") or 0),
        "favorites": int(item.get("favorites") or 0),
        "pictureUrl": item.get("previewUrl"),
        "timeCreated": int(item.get("timeCreated") or 0),
        "timeUpdated": int(item.get("timeUpdated") or 0),
        "fileSize": int(item.get("fileSize") or 0),
        "steamUrl": f"https://steamcommunity.com/sharedfiles/filedetails/?id={item['workshopId']}",
    }


async def browse(list_name: str, offset: int = 0) -> dict[str, Any]:
    page = offset // PAGE_SIZE + 1
    params = {
        "appid": APP_ID,
        "browsesort": _SORTS[list_name],
        "section": "readytouseitems",
        "p": str(page),
        "numperpage": str(PAGE_SIZE),
    }
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            response = await client.get(BROWSE_URL, params=params, headers={"User-Agent": "Mozilla/5.0 ExilesGameManager"})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise steam_workshop.WorkshopError(f"Steam Workshop browser request failed: {exc}", 502) from exc
    ids = _extract_ids(response.text)
    details = await steam_workshop.get_details_many(ids)
    ordered = [_map_item(details[item_id]) for item_id in ids if item_id in details]
    return {"results": ordered, "totalCount": _extract_total(response.text, offset + len(ordered))}


async def search(query: str, offset: int = 0) -> dict[str, Any]:
    page = offset // PAGE_SIZE + 1
    params = {
        "appid": APP_ID,
        "searchtext": query,
        "browsesort": "textsearch",
        "section": "readytouseitems",
        "p": str(page),
        "numperpage": str(PAGE_SIZE),
    }
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            response = await client.get(BROWSE_URL, params=params, headers={"User-Agent": "Mozilla/5.0 ExilesGameManager"})
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise steam_workshop.WorkshopError(f"Steam Workshop search failed: {exc}", 502) from exc
    ids = _extract_ids(response.text)
    details = await steam_workshop.get_details_many(ids)
    ordered = [_map_item(details[item_id]) for item_id in ids if item_id in details]
    return {"results": ordered, "totalCount": _extract_total(response.text, offset + len(ordered))}

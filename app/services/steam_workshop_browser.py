import html
import logging
import re
from typing import Any

import httpx

from app.services import steam_workshop

logger = logging.getLogger("egm.steam_workshop_browser")
BROWSE_URL = "https://steamcommunity.com/workshop/browse/"
PAGE_SIZE = 30
_ITEM_PATTERNS = (
    re.compile(r"(?:sharedfiles|workshop)/filedetails/\?id=(\d{6,20})", re.I),
    re.compile(r"data-publishedfileid=[\'\"](\d{6,20})[\'\"]", re.I),
    re.compile(r"publishedfileid[=:%22\'\"]+(\d{6,20})", re.I),
)
_TOTAL_RE = re.compile(r"Showing\s+\d+-\d+\s+of\s+([\d,\.]+)", re.I)

_SORTS = {
    "trending": "trend",
    "latest_added": "mostrecent",
    "latest_updated": "lastupdated",
}


def _extract_ids(page_html: str) -> list[str]:
    found: list[str] = []
    for pattern in _ITEM_PATTERNS:
        for item_id in pattern.findall(page_html):
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


async def _fetch_workshop_html(params: dict[str, str]) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
    }
    async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
        response = await client.get(BROWSE_URL, params=params, headers=headers)
        response.raise_for_status()
        return response.text


def _browse_params(list_name: str, page: int, app_id: str) -> list[dict[str, str]]:
    sort = _SORTS[list_name]
    common = {"appid": str(app_id), "p": str(page), "numperpage": str(PAGE_SIZE), "l": "english"}
    primary = {**common, "browsesort": sort, "actualsort": sort, "section": "readytouseitems"}
    if list_name == "trending":
        primary["days"] = "7"
    return [
        primary,
        {**common, "browsesort": sort, "section": "readytouseitems"},
        {**common, "browsesort": sort},
        common,
    ]


async def _load_ids_with_fallback(params_list: list[dict[str, str]], *, operation: str) -> tuple[list[str], str]:
    last_html = ""
    last_error: httpx.HTTPError | None = None
    for index, params in enumerate(params_list, start=1):
        try:
            page_html = await _fetch_workshop_html(params)
        except httpx.HTTPError as exc:
            last_error = exc
            logger.warning("Steam Workshop %s request attempt %s failed: %s", operation, index, exc)
            continue
        last_html = page_html
        ids = _extract_ids(page_html)
        if ids:
            logger.info(
                "Steam Workshop %s resolved %s item ids for app %s on attempt %s.",
                operation, len(ids), params.get("appid"), index,
            )
            return ids, page_html
        logger.warning(
            "Steam Workshop %s returned no item ids for app %s on attempt %s (htmlBytes=%s).",
            operation, params.get("appid"), index, len(page_html.encode("utf-8", errors="ignore")),
        )
    if last_error is not None and not last_html:
        raise steam_workshop.WorkshopError(f"Steam Workshop {operation} failed: {last_error}", 502) from last_error
    return [], last_html


async def browse(list_name: str, offset: int = 0, *, app_id: str = steam_workshop.PALWORLD_APP_ID, details_loader=None) -> dict[str, Any]:
    page = offset // PAGE_SIZE + 1
    ids, page_html = await _load_ids_with_fallback(_browse_params(list_name, page, str(app_id)), operation="browser")
    loader = details_loader or steam_workshop.get_details_many
    details = await loader(ids)
    ordered = [_map_item(details[item_id]) for item_id in ids if item_id in details]
    logger.info("Steam Workshop browser app %s returned %s mapped results from %s ids.", app_id, len(ordered), len(ids))
    return {"results": ordered, "totalCount": _extract_total(page_html, offset + len(ordered))}


async def search(query: str, offset: int = 0, *, app_id: str = steam_workshop.PALWORLD_APP_ID, details_loader=None) -> dict[str, Any]:
    page = offset // PAGE_SIZE + 1
    common = {"appid": str(app_id), "searchtext": query, "p": str(page), "numperpage": str(PAGE_SIZE), "l": "english"}
    attempts = [
        {**common, "browsesort": "textsearch", "actualsort": "textsearch", "section": "readytouseitems"},
        {**common, "browsesort": "textsearch", "section": "readytouseitems"},
        {**common, "browsesort": "textsearch"},
        common,
    ]
    ids, page_html = await _load_ids_with_fallback(attempts, operation="search")
    loader = details_loader or steam_workshop.get_details_many
    details = await loader(ids)
    ordered = [_map_item(details[item_id]) for item_id in ids if item_id in details]
    logger.info("Steam Workshop search app %s returned %s mapped results from %s ids.", app_id, len(ordered), len(ids))
    return {"results": ordered, "totalCount": _extract_total(page_html, offset + len(ordered))}


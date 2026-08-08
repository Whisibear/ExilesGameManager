from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from app.games.registry import require_game
from app.services import activity_log, mods_store, steamcmd
from app.services.steam_workshop import DETAILS_URL, WorkshopError, clean_workshop_description, parse_workshop_id

logger = logging.getLogger("egm.conan_workshop")

CONAN_WORKSHOP_APP_ID = "440900"
CONAN_SERVER_APP_ID = "443030"
MODS_RELATIVE_PATH = Path("ConanSandbox") / "Mods"
MODLIST_NAME = "modlist.txt"


def _source(instance: dict[str, Any]) -> str:
    return str(instance.get("name") or "Conan Exiles")


def _assert_conan(instance: dict[str, Any]) -> None:
    game = require_game(instance.get("gameId"))
    if game.family != "conan_exiles":
        raise WorkshopError("The selected server is not a Conan Exiles server.", 409)
    if str(game.steam_workshop_app_id or "") != CONAN_WORKSHOP_APP_ID:
        raise WorkshopError("The selected Conan provider has no supported Steam Workshop catalog.", 409)


def mods_root(instance: dict[str, Any]) -> Path:
    _assert_conan(instance)
    return Path(instance["serverPath"]) / MODS_RELATIVE_PATH


def modlist_path(instance: dict[str, Any]) -> Path:
    return mods_root(instance) / MODLIST_NAME


def _metadata_from_item(item: dict[str, Any], workshop_id: str) -> dict[str, Any]:
    consumer_app_id = str(item.get("consumer_app_id") or item.get("consumer_appid") or "")
    if consumer_app_id and consumer_app_id != CONAN_WORKSHOP_APP_ID:
        raise WorkshopError("This Workshop item does not belong to Conan Exiles.", 400)
    return {
        "workshopId": workshop_id,
        "title": item.get("title") or f"Workshop {workshop_id}",
        "description": clean_workshop_description(item.get("description") or ""),
        "previewUrl": item.get("preview_url") or None,
        "fileSize": int(item.get("file_size") or 0),
        "timeCreated": int(item.get("time_created") or 0),
        "timeUpdated": int(item.get("time_updated") or 0),
        "owner": str(item.get("creator") or "Unknown"),
        "subscriptions": int(item.get("subscriptions") or 0),
        "favorites": int(item.get("favorited") or item.get("favorites") or 0),
        "tags": item.get("tags") or [],
        "dependencies": [
            str(child.get("publishedfileid"))
            for child in item.get("children", [])
            if child.get("publishedfileid")
        ],
    }


async def get_details(instance: dict[str, Any], value: str | int) -> dict[str, Any]:
    _assert_conan(instance)
    workshop_id = parse_workshop_id(value)
    payload = {"itemcount": "1", "publishedfileids[0]": workshop_id}
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.post(DETAILS_URL, data=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise WorkshopError(f"Steam Workshop metadata request failed: {exc}", 502) from exc
    items = data.get("response", {}).get("publishedfiledetails", [])
    if not items:
        raise WorkshopError("Steam did not return this Workshop item.", 404)
    item = items[0]
    if int(item.get("result", 0)) != 1:
        raise WorkshopError("The Workshop item is unavailable, private, or removed.", 404)
    return _metadata_from_item(item, workshop_id)


async def get_details_many(instance: dict[str, Any], values: list[str]) -> dict[str, dict[str, Any]]:
    _assert_conan(instance)
    ids: list[str] = []
    for value in values:
        workshop_id = parse_workshop_id(value)
        if workshop_id not in ids:
            ids.append(workshop_id)
    if not ids:
        return {}
    payload: dict[str, str] = {"itemcount": str(len(ids))}
    for index, workshop_id in enumerate(ids):
        payload[f"publishedfileids[{index}]"] = workshop_id
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.post(DETAILS_URL, data=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise WorkshopError(f"Steam Workshop update check failed: {exc}", 502) from exc
    result: dict[str, dict[str, Any]] = {}
    for item in data.get("response", {}).get("publishedfiledetails", []):
        workshop_id = str(item.get("publishedfileid") or "")
        if not workshop_id or int(item.get("result", 0)) != 1:
            continue
        try:
            result[workshop_id] = _metadata_from_item(item, workshop_id)
        except WorkshopError:
            continue
    return result


def workshop_library_root(instance: dict[str, Any]) -> Path:
    _assert_conan(instance)
    return Path(instance["serverPath"]).resolve() / "steamapps" / "workshop" / "content" / CONAN_WORKSHOP_APP_ID


def download_path(instance: dict[str, Any], workshop_id: str) -> Path:
    return workshop_library_root(instance) / parse_workshop_id(workshop_id)


def _pak_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((p for p in root.rglob("*.pak") if p.is_file()), key=lambda p: p.name.casefold())


async def download(instance: dict[str, Any], workshop_id: str, *, force: bool = False) -> Path:
    _assert_conan(instance)
    workshop_id = parse_workshop_id(workshop_id)
    existing = download_path(instance, workshop_id)
    if existing.is_dir() and _pak_files(existing) and not force:
        return existing
    exe = await steamcmd.ensure_steamcmd()
    server_root = Path(instance["serverPath"]).resolve()
    server_root.mkdir(parents=True, exist_ok=True)
    args = [
        str(exe),
        "+force_install_dir", str(server_root),
        "+login", "anonymous",
        "+app_info_update", "1",
        "+app_info_print", CONAN_SERVER_APP_ID,
        "+app_info_print", CONAN_WORKSHOP_APP_ID,
        "+workshop_download_item", CONAN_WORKSHOP_APP_ID, workshop_id,
        "validate",
        "+quit",
    ]
    returncode = await steamcmd._run(args)
    if returncode != 0:
        raise WorkshopError(
            f"Anonymous SteamCMD download failed for Conan Exiles Workshop item {workshop_id} (exit code {returncode}).",
            502,
        )
    if not existing.is_dir():
        raise WorkshopError("SteamCMD completed, but the Conan Workshop download directory was not found.", 502)
    if not _pak_files(existing):
        raise WorkshopError("The Workshop item contains no Conan Exiles .pak mod file.", 422)
    return existing


def _entry_pak_paths(instance: dict[str, Any], mod: dict[str, Any]) -> list[Path]:
    workshop_id = str(mod.get("workshopId") or "").strip()
    if workshop_id:
        cached = _pak_files(download_path(instance, workshop_id))
        if cached:
            return cached
    installed = mod.get("installedPaths")
    if isinstance(installed, list):
        return [Path(str(path)) for path in installed if str(path).lower().endswith(".pak")]
    return []


def _write_modlist(instance: dict[str, Any], mods: list[dict[str, Any]]) -> None:
    root = mods_root(instance)
    root.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    seen: set[str] = set()
    for mod in mods_store.sorted_mods(mods):
        if mod.get("status") != "enabled" or not mod.get("workshopId"):
            continue
        for pak_path in _entry_pak_paths(instance, mod):
            resolved = pak_path.resolve()
            key = str(resolved).casefold()
            if key in seen:
                continue
            seen.add(key)
            lines.append(str(resolved))
    path = modlist_path(instance)
    temp = path.with_suffix(".tmp")
    temp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    temp.replace(path)


def install_from_download(
    instance: dict[str, Any],
    details: dict[str, Any],
    downloaded: Path,
    *,
    existing: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pak_files = _pak_files(downloaded)
    if not pak_files:
        raise WorkshopError("The Workshop item contains no Conan Exiles .pak mod file.", 422)
    return {
        "id": (existing or {}).get("id") or f"conan-workshop-{details['workshopId']}",
        "name": details.get("title") or f"Workshop {details['workshopId']}",
        "version": str(details.get("timeUpdated") or "Workshop"),
        "author": details.get("owner") or "Steam Workshop",
        "description": details.get("description") or "",
        "dependencies": details.get("dependencies") or [],
        "status": (existing or {}).get("status") or "enabled",
        "loadPriority": int((existing or {}).get("loadPriority") or 1),
        "updateAvailable": False,
        "latestVersion": str(details.get("timeUpdated") or ""),
        "source": "steam_workshop",
        "workshopId": str(details["workshopId"]),
        "packageName": pak_files[0].stem,
        "installedUpdatedAt": int(details.get("timeUpdated") or 0),
        "previewUrl": details.get("previewUrl"),
        "installKind": "conan_workshop_reference",
        "pakNames": [path.name for path in pak_files],
        "installedPaths": [str(path.resolve()) for path in pak_files],
        "workshopContentPath": str(downloaded.resolve()),
        "deploymentStatus": "configured",
        "deploymentMessage": "Referenced from the server-local Steam Workshop library in ConanSandbox/Mods/modlist.txt. Restart Conan to apply changes.",
    }


async def install(instance: dict[str, Any], workshop_id: str, *, force_download: bool = False) -> list[dict[str, Any]]:
    _assert_conan(instance)
    workshop_id = parse_workshop_id(workshop_id)
    source = _source(instance)
    details = await get_details(instance, workshop_id)
    activity_log.log("info", source, f"Conan Workshop item {workshop_id} download started: {details['title']}.", instance_id=instance["id"])
    downloaded = await download(instance, workshop_id, force=force_download)
    mods = mods_store.load_mods(instance["id"])
    existing = next((mod for mod in mods if str(mod.get("workshopId")) == workshop_id), None)
    entry = install_from_download(instance, details, downloaded, existing=existing)
    if existing:
        entry["loadPriority"] = int(existing.get("loadPriority") or 1)
        mods = [entry if mod.get("id") == existing.get("id") else mod for mod in mods]
    else:
        entry["loadPriority"] = len(mods) + 1
        mods.append(entry)
    mods_store.save_mods(instance["id"], mods)
    _write_modlist(instance, mods)
    activity_log.log("info", source, f"Conan Workshop mod installed and enabled: {entry['name']} ({workshop_id}).", instance_id=instance["id"])
    return await with_update_status(mods_store.sorted_mods(mods), instance)


def set_enabled(instance: dict[str, Any], mod_id: str, enabled: bool) -> list[dict[str, Any]]:
    _assert_conan(instance)
    mods = mods_store.load_mods(instance["id"])
    target = next((mod for mod in mods if mod.get("id") == mod_id), None)
    if not target:
        raise WorkshopError("Conan Workshop mod not found.", 404)
    target["status"] = "enabled" if enabled else "disabled"
    target["deploymentStatus"] = "configured" if enabled else "disabled"
    target["deploymentMessage"] = "Restart the server to apply the Conan mod list change."
    mods_store.save_mods(instance["id"], mods)
    _write_modlist(instance, mods)
    activity_log.log(
        "info",
        _source(instance),
        f"Conan Workshop mod {'enabled' if enabled else 'disabled'}: {target.get('name') or mod_id}.",
        instance_id=instance["id"],
    )
    return mods_store.sorted_mods(mods)


def reorder(instance: dict[str, Any], ordered_ids: list[str]) -> list[dict[str, Any]]:
    _assert_conan(instance)
    mods = mods_store.load_mods(instance["id"])
    order = {mod_id: index + 1 for index, mod_id in enumerate(ordered_ids)}
    for mod in mods:
        if mod.get("id") in order:
            mod["loadPriority"] = order[mod["id"]]
    mods_store.save_mods(instance["id"], mods)
    _write_modlist(instance, mods)
    activity_log.log("info", _source(instance), "Conan Workshop mod load order updated.", instance_id=instance["id"])
    return mods_store.sorted_mods(mods)


def remove(instance: dict[str, Any], mod_id: str) -> list[dict[str, Any]]:
    _assert_conan(instance)
    mods = mods_store.load_mods(instance["id"])
    target = next((mod for mod in mods if mod.get("id") == mod_id), None)
    if not target:
        raise WorkshopError("Conan Workshop mod not found.", 404)
    mods = [mod for mod in mods if mod.get("id") != mod_id]
    for index, mod in enumerate(mods_store.sorted_mods(mods), start=1):
        mod["loadPriority"] = index
    mods_store.save_mods(instance["id"], mods)
    _write_modlist(instance, mods)
    activity_log.log("info", _source(instance), f"Conan Workshop mod removed: {target.get('name') or mod_id}.", instance_id=instance["id"])
    return mods_store.sorted_mods(mods)


async def with_update_status(mods: list[dict[str, Any]], instance: dict[str, Any]) -> list[dict[str, Any]]:
    workshop = [str(mod.get("workshopId")) for mod in mods if mod.get("workshopId")]
    details_by_id: dict[str, dict[str, Any]] = {}
    if workshop:
        try:
            details_by_id = await get_details_many(instance, workshop)
        except WorkshopError:
            details_by_id = {}
    result: list[dict[str, Any]] = []
    metadata_changed = False
    for mod in mods_store.sorted_mods(mods):
        enriched = dict(mod)
        wid = str(mod.get("workshopId") or "")
        if wid:
            cached_root = download_path(instance, wid)
            cached_paks = _pak_files(cached_root)
            if cached_paks:
                cache_paths = [str(path.resolve()) for path in cached_paks]
                if list(enriched.get("installedPaths") or []) != cache_paths or enriched.get("installKind") != "conan_workshop_reference":
                    enriched["installedPaths"] = cache_paths
                    enriched["pakNames"] = [path.name for path in cached_paks]
                    enriched["packageName"] = cached_paks[0].stem
                    enriched["workshopContentPath"] = str(cached_root.resolve())
                    enriched["installKind"] = "conan_workshop_reference"
                    enriched["deploymentMessage"] = "Referenced from the server-local Steam Workshop library in ConanSandbox/Mods/modlist.txt. Restart Conan to apply changes."
                    metadata_changed = True
        details = details_by_id.get(wid)
        if details:
            latest = int(details.get("timeUpdated") or 0)
            installed = int(enriched.get("installedUpdatedAt") or 0)
            enriched.update({
                "name": details.get("title") or enriched.get("name"),
                "description": details.get("description") or enriched.get("description", ""),
                "previewUrl": details.get("previewUrl") or enriched.get("previewUrl"),
                "latestVersion": str(latest),
                "updateAvailable": bool(installed and latest > installed),
            })
        result.append(enriched)
    if metadata_changed:
        mods_store.save_mods(instance["id"], result)
        _write_modlist(instance, result)
        activity_log.log("info", _source(instance), "Refreshed Conan Workshop mod references from the server-local Workshop library.", instance_id=instance["id"])
    return result


async def check_updates(instance: dict[str, Any]) -> dict[str, Any]:
    _assert_conan(instance)
    mods = mods_store.load_mods(instance["id"])
    workshop_mods = [mod for mod in mods if mod.get("workshopId")]
    source = _source(instance)
    if not workshop_mods:
        activity_log.log("info", source, "Conan Workshop update check completed: no mods installed.", instance_id=instance["id"])
        return {"checked": 0, "updatesAvailable": 0, "upToDate": True, "mods": []}
    details_by_id = await get_details_many(instance, [str(mod["workshopId"]) for mod in workshop_mods])
    checked_at = int(time.time())
    updates = 0
    result: list[dict[str, Any]] = []
    for mod in workshop_mods:
        enriched = dict(mod)
        wid = str(mod["workshopId"])
        details = details_by_id.get(wid)
        if not details:
            enriched["updateCheckError"] = "Steam did not return this Conan Workshop item."
            result.append(enriched)
            continue
        latest = int(details.get("timeUpdated") or 0)
        installed = int(mod.get("installedUpdatedAt") or 0)
        if installed <= 0:
            installed = latest
            enriched["installedUpdatedAt"] = latest
        update_available = latest > installed
        updates += int(update_available)
        enriched.update({
            "name": details.get("title") or enriched.get("name"),
            "description": details.get("description") or enriched.get("description", ""),
            "previewUrl": details.get("previewUrl") or enriched.get("previewUrl"),
            "latestVersion": str(latest),
            "updateAvailable": update_available,
            "lastUpdateCheckedAt": checked_at,
        })
        result.append(enriched)
    by_id = {str(mod.get("id")): mod for mod in result}
    saved = [by_id.get(str(mod.get("id")), mod) for mod in mods]
    mods_store.save_mods(instance["id"], saved)
    activity_log.log("info", source, f"Conan Workshop update check completed: {updates} update(s) available.", instance_id=instance["id"])
    return {"checked": len(workshop_mods), "updatesAvailable": updates, "upToDate": updates == 0, "mods": result}


async def update_all(instance: dict[str, Any]) -> dict[str, Any]:
    check = await check_updates(instance)
    targets = [mod for mod in check["mods"] if mod.get("updateAvailable") and mod.get("workshopId")]
    updated: list[str] = []
    for mod in targets:
        wid = str(mod["workshopId"])
        await install(instance, wid, force_download=True)
        updated.append(wid)
    mods = await with_update_status(mods_store.load_mods(instance["id"]), instance)
    return {"updated": len(updated), "updatedIds": updated, "backup": None, "mods": mods}


async def scan_downloaded_cache(instance: dict[str, Any]) -> list[dict[str, Any]]:
    _assert_conan(instance)
    root = workshop_library_root(instance)
    if not root.is_dir():
        return []
    stored = {str(mod.get("workshopId")): mod for mod in mods_store.load_mods(instance["id"]) if mod.get("workshopId")}
    ids = [child.name for child in root.iterdir() if child.is_dir() and child.name.isdigit() and _pak_files(child)]
    details = await get_details_many(instance, ids) if ids else {}
    items: list[dict[str, Any]] = []
    for wid in ids:
        metadata = details.get(wid, {})
        current = stored.get(wid)
        remote_updated = int(metadata.get("timeUpdated") or 0)
        installed_updated = int((current or {}).get("installedUpdatedAt") or 0)
        items.append({
            "workshopId": wid,
            "name": metadata.get("title") or f"Workshop {wid}",
            "author": metadata.get("owner") or "Steam Workshop",
            "previewUrl": metadata.get("previewUrl"),
            "valid": True,
            "validationError": None,
            "status": "update_available" if current and installed_updated and remote_updated > installed_updated else "installed" if current else "downloaded",
            "path": str(download_path(instance, wid).resolve()),
            "pakPaths": [str(path.resolve()) for path in _pak_files(download_path(instance, wid))],
        })
    return items


async def install_from_cache(instance: dict[str, Any], workshop_id: str) -> list[dict[str, Any]]:
    _assert_conan(instance)
    wid = parse_workshop_id(workshop_id)
    downloaded = download_path(instance, wid)
    if not downloaded.is_dir() or not _pak_files(downloaded):
        raise WorkshopError("Conan Workshop item was not found in the SteamCMD cache.", 404)
    details = await get_details(instance, wid)
    mods = mods_store.load_mods(instance["id"])
    existing = next((mod for mod in mods if str(mod.get("workshopId")) == wid), None)
    entry = install_from_download(instance, details, downloaded, existing=existing)
    if existing:
        entry["loadPriority"] = int(existing.get("loadPriority") or 1)
        mods = [entry if mod.get("id") == existing.get("id") else mod for mod in mods]
    else:
        entry["loadPriority"] = len(mods) + 1
        mods.append(entry)
    mods_store.save_mods(instance["id"], mods)
    _write_modlist(instance, mods)
    activity_log.log("info", _source(instance), f"Cached Conan Workshop mod installed: {entry['name']} ({wid}).", instance_id=instance["id"])
    return await with_update_status(mods_store.sorted_mods(mods), instance)

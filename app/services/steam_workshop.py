from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import time
from pathlib import Path
from typing import Any

import httpx

from app.paths import data_dir
from app.services import activity_log, backup_service, mods_store, pal_mod_settings, steamcmd

logger = logging.getLogger("egm.steam_workshop")
PALWORLD_APP_ID = "1623730"
DETAILS_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
WORKSHOP_ID_RE = re.compile(r"(?:[?&]id=)?(?P<id>\d{6,20})")
STAGING_ROOT = data_dir() / "workshop_staging"
STAGING_ROOT.mkdir(parents=True, exist_ok=True)

BBCODE_RE = re.compile(r"\[/?(?:h[1-6]|b|i|u|list|\*|url(?:=[^\]]+)?|quote|code)\]", re.IGNORECASE)

def clean_workshop_description(value: str) -> str:
    text = BBCODE_RE.sub("", value or "")
    return re.sub(r"\s+", " ", text).strip()


class WorkshopError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.technical_details: str | None = None


def parse_workshop_id(value: str | int) -> str:
    match = WORKSHOP_ID_RE.search(str(value).strip())
    if not match:
        raise WorkshopError("Enter a valid Steam Workshop URL or Workshop ID.", 400)
    return match.group("id")


async def get_details(workshop_id: str) -> dict[str, Any]:
    workshop_id = parse_workshop_id(workshop_id)
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
    consumer_app_id = str(item.get("consumer_app_id") or item.get("consumer_appid") or "")
    if consumer_app_id and consumer_app_id != PALWORLD_APP_ID:
        raise WorkshopError("This Workshop item does not belong to Palworld.", 400)
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
        "dependencies": [str(c.get("publishedfileid")) for c in item.get("children", []) if c.get("publishedfileid")],
    }


async def get_details_many(workshop_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Fetch current Steam Workshop metadata for several items in one request."""
    normalized: list[str] = []
    for value in workshop_ids:
        workshop_id = parse_workshop_id(value)
        if workshop_id not in normalized:
            normalized.append(workshop_id)
    if not normalized:
        return {}

    payload: dict[str, str] = {"itemcount": str(len(normalized))}
    for index, workshop_id in enumerate(normalized):
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
        consumer_app_id = str(item.get("consumer_app_id") or item.get("consumer_appid") or "")
        if consumer_app_id and consumer_app_id != PALWORLD_APP_ID:
            continue
        result[workshop_id] = {
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
            "dependencies": [str(c.get("publishedfileid")) for c in item.get("children", []) if c.get("publishedfileid")],
        }
    return result


def workshop_root(server_path: str | Path) -> Path:
    return Path(server_path) / "Mods" / "Workshop"


def _library_roots(server_path: str | Path | None = None) -> list[Path]:
    roots: list[Path] = []
    if server_path:
        server_root = Path(server_path).resolve()
        roots.extend([server_root, server_root.parent])
    roots.extend([steamcmd.STEAMCMD_DIR, data_dir() / "steamcmd"])

    unique: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def _download_candidates(
    workshop_id: str,
    server_path: str | Path | None = None,
) -> list[Path]:
    candidates: list[Path] = []
    for root in _library_roots(server_path):
        candidates.extend([
            root / "steamapps" / "workshop" / "content" / PALWORLD_APP_ID / workshop_id,
            root / "steamapps" / "workshop" / "downloads" / PALWORLD_APP_ID / workshop_id,
            root / "workshop" / "content" / PALWORLD_APP_ID / workshop_id,
            root / "workshop" / "downloads" / PALWORLD_APP_ID / workshop_id,
        ])

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _clear_partial_download(
    workshop_id: str,
    server_path: str | Path | None = None,
) -> None:
    """Remove only incomplete state for one Workshop download."""
    for candidate in _download_candidates(workshop_id, server_path):
        normalized = str(candidate).replace("\\", "/").lower()
        if "/workshop/downloads/" in normalized and candidate.exists():
            shutil.rmtree(candidate, ignore_errors=True)


def _locate_download(
    workshop_id: str,
    server_path: str | Path | None = None,
) -> Path:
    for candidate in _download_candidates(workshop_id, server_path):
        if candidate.is_dir():
            return candidate

    for root in _library_roots(server_path):
        if not root.is_dir():
            continue
        for candidate in root.glob(
            f"**/workshop/content/{PALWORLD_APP_ID}/{workshop_id}"
        ):
            if candidate.is_dir():
                return candidate
    raise WorkshopError(
        "SteamCMD completed, but no downloaded Workshop content was found.",
        502,
    )

def _read_info(mod_dir: Path) -> dict[str, Any]:
    info_path = mod_dir / "Info.json"
    if not info_path.is_file():
        nested = list(mod_dir.glob("*/Info.json"))
        if len(nested) == 1:
            mod_dir = nested[0].parent
            info_path = nested[0]
        else:
            raise WorkshopError("The Workshop item is not a Palworld server mod: Info.json is missing.")
    try:
        info = json.loads(info_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise WorkshopError(f"Info.json is invalid: {exc}") from exc
    package_name = str(info.get("PackageName") or info.get("packageName") or "").strip()
    if not package_name or not re.fullmatch(r"[A-Za-z0-9_.-]+", package_name):
        raise WorkshopError("Info.json contains no valid PackageName.")
    is_server = info.get("IsServer", info.get("isServer", True))
    if is_server is False:
        raise WorkshopError("This Workshop mod is marked as client-only and cannot be installed on the server.")
    rules = info.get("InstallRules", info.get("installRules", []))
    return {"packageName": package_name, "info": info, "rules": rules, "sourceDir": mod_dir}


def inspect_installed(server_path: str | Path, workshop_id: str) -> dict[str, Any]:
    mod_dir = workshop_root(server_path) / parse_workshop_id(workshop_id)
    if not mod_dir.is_dir():
        raise WorkshopError("The Workshop mod is not installed.", 404)
    return _read_info(mod_dir)


async def download(
    workshop_id: str,
    *,
    server_path: str | Path | None = None,
    force: bool = False,
) -> Path:
    workshop_id = parse_workshop_id(workshop_id)

    try:
        existing = _locate_download(workshop_id, server_path)
        _read_info(existing)
        if not force:
            logger.info("workshop %s: using existing validated Workshop download", workshop_id)
            return existing
        if server_path:
            installed = workshop_root(server_path) / workshop_id
            cache_mtime = max((entry.stat().st_mtime for entry in existing.rglob("*") if entry.is_file()), default=existing.stat().st_mtime)
            installed_mtime = max((entry.stat().st_mtime for entry in installed.rglob("*") if entry.is_file()), default=0.0) if installed.is_dir() else 0.0
            if cache_mtime > installed_mtime:
                logger.info("workshop %s: using newer manually downloaded SteamCMD cache", workshop_id)
                return existing
    except (WorkshopError, OSError):
        pass

    exe = await steamcmd.ensure_steamcmd()
    attempts: list[str] = []
    command_sets: list[tuple[str, list[str]]] = []

    if server_path:
        server_root = Path(server_path).resolve()
        server_root.mkdir(parents=True, exist_ok=True)
        command_sets.append((
            "instance-library",
            [
                str(exe),
                "+force_install_dir",
                str(server_root),
                "+login",
                "anonymous",
                "+app_info_update",
                "1",
                "+app_info_print",
                steamcmd.PALSERVER_APP_ID,
                "+app_info_print",
                PALWORLD_APP_ID,
                "+workshop_download_item",
                PALWORLD_APP_ID,
                workshop_id,
                "validate",
                "+quit",
            ],
        ))

    command_sets.append((
        "legacy-global-library",
        [
            str(exe),
            "+login",
            "anonymous",
            "+workshop_download_item",
            PALWORLD_APP_ID,
            workshop_id,
            "validate",
            "+quit",
        ],
    ))

    last_returncode = 0
    last_output: list[str] = []
    for index, (label, args) in enumerate(command_sets):
        output: list[str] = []

        def capture(line: str) -> None:
            output.append(line)

        if index:
            _clear_partial_download(workshop_id, server_path)
            await asyncio.sleep(0.5)

        returncode = await steamcmd._run(args, capture)
        last_returncode = returncode
        last_output = output
        technical = "\n".join(output[-200:]).strip()
        attempts.append(
            f"{label} (SteamCMD exit code: {returncode})\n{technical}"
        )

        try:
            downloaded = _locate_download(workshop_id, server_path)
            _read_info(downloaded)
            logger.info(
                "workshop %s: anonymous download succeeded via %s",
                workshop_id,
                label,
            )
            return downloaded
        except WorkshopError:
            joined = "\n".join(output).lower()
            if "missing decryption key" in joined:
                logger.warning(
                    "workshop %s: %s did not receive a depot key; trying the next anonymous library context",
                    workshop_id,
                    label,
                )
            elif "download item" in joined and "failed" in joined:
                logger.warning(
                    "workshop %s: %s failed; trying the next anonymous library context",
                    workshop_id,
                    label,
                )

    joined = "\n".join(last_output).lower()

    if "missing decryption key" in joined:
        message = (
            f"Anonymous SteamCMD download failed for Workshop item {workshop_id}. "
            "Open the normal SteamCMD console on the Mods page, sign in there, run the Workshop download command, then retry the install or update."
        )
    elif "download item" in joined and "failed" in joined:
        message = (
            f"Anonymous SteamCMD download failed for Workshop item {workshop_id}. "
            "Open the normal SteamCMD console on the Mods page, download the item there, then retry."
        )
    elif last_returncode != 0:
        message = (
            f"SteamCMD exited with code {last_returncode} while downloading Workshop item {workshop_id}."
        )
    else:
        message = (
            f"Workshop item {workshop_id} was not found after SteamCMD completed both anonymous download strategies."
        )

    error = WorkshopError(message, 502)
    error.technical_details = (
        "\n\n".join(attempts)
        + "\n\nSearched: "
        + "; ".join(map(str, _download_candidates(workshop_id, server_path)))
    )
    raise error

def install_from_download(instance: dict[str, Any], details: dict[str, Any], downloaded_dir: Path) -> dict[str, Any]:
    workshop_id = details["workshopId"]
    staged = STAGING_ROOT / f"{workshop_id}-{int(time.time())}"
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(downloaded_dir, staged)
    inspected = _read_info(staged)
    source_dir = inspected["sourceDir"]
    destination = workshop_root(instance["serverPath"]) / workshop_id
    destination.parent.mkdir(parents=True, exist_ok=True)
    backup = destination.with_name(f".{destination.name}.rollback")
    if backup.exists():
        shutil.rmtree(backup)
    try:
        if destination.exists():
            destination.rename(backup)
        shutil.copytree(source_dir, destination)
        pal_mod_settings.set_enabled(instance["serverPath"], inspected["packageName"], True)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        if backup.exists():
            backup.rename(destination)
        raise
    finally:
        shutil.rmtree(staged, ignore_errors=True)

    return {
        "id": f"workshop-{workshop_id}",
        "name": details["title"],
        "version": str(details.get("timeUpdated") or "Workshop"),
        "author": details.get("owner") or "Steam Workshop",
        "description": details.get("description") or "",
        "dependencies": details.get("dependencies", []),
        "status": "enabled",
        "loadPriority": 0,
        "updateAvailable": False,
        "latestVersion": None,
        "source": "steam_workshop",
        "workshopId": workshop_id,
        "packageName": inspected["packageName"],
        "installedUpdatedAt": details.get("timeUpdated") or 0,
        "previewUrl": details.get("previewUrl"),
        "installKind": "workshop",
        "folderName": workshop_id,
        "deploymentStatus": "configured",
        "deploymentMessage": "Server start required. The mod will be deployed on the next manual server start.",
    }


def deployment_manifest(server_path: str | Path, package_name: str) -> Path:
    return Path(server_path) / "Mods" / "ManagedMods" / package_name / "InstallManifest.json"


def deployment_state(server_path: str | Path, package_name: str, enabled: bool = True) -> tuple[str, str]:
    if not enabled:
        return "disabled", "Mod is disabled."
    if deployment_manifest(server_path, package_name).is_file():
        return "deployed", "Palworld created the managed installation manifest."
    return "configured", "Mod is configured and awaiting Palworld deployment."


async def install(instance: dict[str, Any], workshop_id: str, *, force_download: bool = False) -> list[dict[str, Any]]:
    details = await get_details(workshop_id)
    activity_log.log("info", instance.get("name") or "Workshop", f"Downloading Workshop item {details['workshopId']} ({details['title']}).")
    downloaded = await download(
        details["workshopId"],
        server_path=instance["serverPath"],
        force=force_download,
    )
    entry = install_from_download(instance, details, downloaded)
    activity_log.log("info", instance.get("name") or "Workshop", f"Workshop item {details['workshopId']} installed as package {entry['packageName']}.")
    mods = mods_store.load_mods(instance["id"])
    existing = next((m for m in mods if str(m.get("workshopId")) == details["workshopId"]), None)
    entry["loadPriority"] = existing.get("loadPriority", len(mods) + 1) if existing else len(mods) + 1
    mods = [entry if existing and m["id"] == existing["id"] else m for m in mods]
    if not existing:
        mods.append(entry)
    mods_store.save_mods(instance["id"], mods)

    activity_log.log(
        "info",
        instance.get("name") or "Workshop",
        f"Workshop mod {entry['packageName']}: installed and configured. Manual server start required.",
    )
    return await with_update_status(mods_store.sorted_mods(mods), instance)


def discover_installed(instance: dict[str, Any], stored_mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Discover only official Steam Workshop server mods from the active server path.

    This intentionally scans <serverPath>/Mods/Workshop only. It never scans the
    general Mods directory, so framework files such as BPModLoaderMod, Shared,
    Mods.json, and Mods.txt cannot appear as separate mods.
    """
    root = workshop_root(instance["serverPath"])
    by_workshop_id = {
        str(mod.get("workshopId")): dict(mod)
        for mod in stored_mods
        if mod.get("workshopId")
    }
    if not root.is_dir():
        return list(by_workshop_id.values())

    changed = False
    for child in root.iterdir():
        if not child.is_dir() or not child.name.isdigit():
            continue
        workshop_id = child.name
        try:
            inspected = _read_info(child)
        except WorkshopError:
            continue
        existing = by_workshop_id.get(workshop_id)
        if existing:
            if existing.get("packageName") != inspected["packageName"]:
                existing["packageName"] = inspected["packageName"]
                changed = True
            existing["folderName"] = workshop_id
            existing["source"] = "steam_workshop"
            existing["installKind"] = "workshop"
            continue
        by_workshop_id[workshop_id] = {
            "id": f"workshop-{workshop_id}",
            "name": inspected["packageName"],
            "version": "Workshop",
            "author": "Steam Workshop",
            "description": "",
            "dependencies": [],
            "status": "enabled" if inspected["packageName"] in pal_mod_settings.active_mods(instance["serverPath"]) else "disabled",
            "loadPriority": len(by_workshop_id) + 1,
            "updateAvailable": False,
            "latestVersion": None,
            "source": "steam_workshop",
            "workshopId": workshop_id,
            "packageName": inspected["packageName"],
            "installedUpdatedAt": 0,
            "previewUrl": None,
            "installKind": "workshop",
            "folderName": workshop_id,
            "deploymentStatus": "configured",
            "deploymentMessage": "Discovered from the active server path. Server start may be required.",
        }
        changed = True

    result = list(by_workshop_id.values())
    if changed or len(result) != len(stored_mods):
        mods_store.save_mods(instance["id"], result)
    return result


async def with_update_status(mods: list[dict[str, Any]], instance: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for mod in mods:
        if not mod.get("workshopId"):
            result.append(mod)
            continue
        enriched = dict(mod)
        if instance and mod.get("packageName"):
            state, message = deployment_state(
                instance["serverPath"],
                str(mod["packageName"]),
                mod.get("status") == "enabled",
            )
            enriched["deploymentStatus"] = state
            enriched["deploymentMessage"] = message
        try:
            details = await get_details(str(mod["workshopId"]))
            latest = int(details.get("timeUpdated") or 0)
            installed = int(mod.get("installedUpdatedAt") or 0)
            enriched.update({"updateAvailable": latest > installed, "latestVersion": str(latest)})
        except WorkshopError:
            pass
        result.append(enriched)
    return result


async def check_updates(instance: dict[str, Any]) -> dict[str, Any]:
    """Compare installed Workshop timestamps with Steam without downloading files."""
    stored = discover_installed(instance, mods_store.load_mods(instance["id"]))
    workshop_mods = [mod for mod in stored if mod.get("workshopId")]
    source = instance.get("name") or "Workshop"

    if not workshop_mods:
        activity_log.log("info", source, "Workshop mod update check completed: no Workshop mods installed.")
        return {"checked": 0, "updatesAvailable": 0, "upToDate": True, "mods": []}

    activity_log.log("info", source, f"Checking {len(workshop_mods)} Workshop mod(s) for updates.")
    details_by_id = await get_details_many([str(mod["workshopId"]) for mod in workshop_mods])
    checked_at = int(time.time())
    updates = 0
    results: list[dict[str, Any]] = []

    for mod in workshop_mods:
        enriched = dict(mod)
        workshop_id = str(mod["workshopId"])
        details = details_by_id.get(workshop_id)
        if not details:
            enriched["updateCheckError"] = "Steam did not return this Workshop item."
            results.append(enriched)
            activity_log.log("warning", source, f"Workshop item {workshop_id}: update check unavailable.")
            continue

        latest = int(details.get("timeUpdated") or 0)
        installed = int(mod.get("installedUpdatedAt") or 0)
        update_available = bool(installed and latest > installed)
        # A discovered item with no stored timestamp is not falsely declared outdated.
        # Its current remote timestamp becomes the baseline for future checks.
        if installed <= 0:
            installed = latest
            enriched["installedUpdatedAt"] = latest

        enriched.update({
            "name": details.get("title") or enriched.get("name"),
            "description": details.get("description") or enriched.get("description", ""),
            "previewUrl": details.get("previewUrl") or enriched.get("previewUrl"),
            "latestVersion": str(latest),
            "updateAvailable": update_available,
            "lastUpdateCheckedAt": checked_at,
        })
        if update_available:
            updates += 1
            activity_log.log("info", source, f"Workshop mod {enriched.get('packageName') or workshop_id}: update available.")
        else:
            activity_log.log("info", source, f"Workshop mod {enriched.get('packageName') or workshop_id}: up to date.")
        results.append(enriched)

    # Preserve non-Workshop records if any ever exist, while updating Workshop metadata.
    by_id = {str(mod.get("id")): mod for mod in results}
    saved = [by_id.get(str(mod.get("id")), mod) for mod in stored]
    mods_store.save_mods(instance["id"], saved)
    activity_log.log("info", source, f"Workshop mod update check completed: {updates} update(s) available.")
    return {
        "checked": len(workshop_mods),
        "updatesAvailable": updates,
        "upToDate": updates == 0,
        "mods": results,
    }



async def update_all(instance: dict[str, Any]) -> dict[str, Any]:
    """Download all available updates before changing server files.

    This prevents failed SteamCMD downloads from creating unnecessary safety
    backups or partially updating a multi-mod set. The server process remains
    unchanged throughout the operation.
    """
    check = await check_updates(instance)
    targets = [m for m in check["mods"] if m.get("updateAvailable") and m.get("workshopId")]
    if not targets:
        return {
            "updated": 0,
            "backup": None,
            "mods": await with_update_status(
                discover_installed(instance, mods_store.load_mods(instance["id"])), instance
            ),
        }

    source = instance.get("name") or "Workshop"
    prepared: list[tuple[dict[str, Any], dict[str, Any], Path]] = []
    activity_log.log("info", source, f"Preparing {len(targets)} Workshop mod update(s).")
    for mod in targets:
        workshop_id = str(mod["workshopId"])
        details = await get_details(workshop_id)
        activity_log.log("info", source, f"Downloading Workshop item {workshop_id} ({details['title']}).")
        downloaded = await download(
            workshop_id,
            server_path=instance["serverPath"],
            force=True,
        )
        prepared.append((mod, details, downloaded))

    backup = await backup_service.backup_before_mod_update(instance)
    activity_log.log(
        "info", source,
        f"All downloads validated. Updating {len(prepared)} Workshop mod(s). Server will remain unchanged.",
    )
    updated_ids: list[str] = []
    mods = mods_store.load_mods(instance["id"])
    for mod, details, downloaded in prepared:
        entry = install_from_download(instance, details, downloaded)
        existing = next((m for m in mods if str(m.get("workshopId")) == details["workshopId"]), None)
        entry["loadPriority"] = existing.get("loadPriority", len(mods) + 1) if existing else len(mods) + 1
        if existing:
            mods = [entry if m.get("id") == existing.get("id") else m for m in mods]
        else:
            mods.append(entry)
        updated_ids.append(details["workshopId"])
        activity_log.log("info", source, f"Workshop item {details['workshopId']} updated successfully.")

    mods_store.save_mods(instance["id"], mods)
    return {
        "updated": len(updated_ids),
        "updatedIds": updated_ids,
        "backup": backup,
        "mods": await with_update_status(mods_store.sorted_mods(mods), instance),
    }




def _tree_latest_mtime(path: Path) -> float:
    try:
        latest = path.stat().st_mtime
    except OSError:
        return 0.0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    latest = max(latest, entry.stat().st_mtime)
                except OSError:
                    continue
    except OSError:
        pass
    return latest


async def scan_downloaded_cache(instance: dict[str, Any]) -> list[dict[str, Any]]:
    """Return valid Workshop items already downloaded by the external SteamCMD console."""
    by_id: dict[str, Path] = {}
    for root in _library_roots(instance.get("serverPath")):
        content_root = root / "steamapps" / "workshop" / "content" / PALWORLD_APP_ID
        if not content_root.is_dir():
            continue
        try:
            children = list(content_root.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir() and child.name.isdigit():
                by_id.setdefault(child.name, child)

    if not by_id:
        return []

    details_by_id: dict[str, dict[str, Any]] = {}
    try:
        details_by_id = await get_details_many(list(by_id))
    except WorkshopError:
        details_by_id = {}

    stored = mods_store.load_mods(instance["id"])
    installed_by_id = {
        str(mod.get("workshopId")): mod
        for mod in stored
        if mod.get("workshopId")
    }
    result: list[dict[str, Any]] = []
    for workshop_id, source in sorted(by_id.items(), key=lambda item: item[0]):
        details = details_by_id.get(workshop_id, {})
        try:
            inspected = _read_info(source)
            package_name = inspected["packageName"]
            valid = True
            validation_error = None
        except WorkshopError as exc:
            package_name = None
            valid = False
            validation_error = exc.message

        installed = installed_by_id.get(workshop_id)
        installed_dir = workshop_root(instance["serverPath"]) / workshop_id
        cache_mtime = _tree_latest_mtime(source)
        installed_mtime = _tree_latest_mtime(installed_dir) if installed_dir.is_dir() else 0.0
        if not valid:
            status = "invalid"
        elif not installed or not installed_dir.is_dir():
            status = "ready"
        elif cache_mtime > installed_mtime + 0.5:
            status = "update_available"
        else:
            status = "installed"

        result.append({
            "workshopId": workshop_id,
            "name": details.get("title") or package_name or f"Workshop {workshop_id}",
            "author": details.get("owner") or "Steam Workshop",
            "description": details.get("description") or "",
            "previewUrl": details.get("previewUrl"),
            "packageName": package_name,
            "status": status,
            "valid": valid,
            "validationError": validation_error,
            "sourcePath": str(source),
            "sizeBytes": sum(
                entry.stat().st_size
                for entry in source.rglob("*")
                if entry.is_file()
            ),
            "downloadedAt": int(cache_mtime),
            "installedUpdatedAt": int(installed_mtime),
        })
    return result


def set_mod_enabled(instance: dict[str, Any], mod: dict[str, Any], enabled: bool) -> None:
    package_name = str(mod.get("packageName") or "").strip()
    if not package_name:
        inspected = inspect_installed(instance["serverPath"], str(mod["workshopId"]))
        package_name = inspected["packageName"]
        mod["packageName"] = package_name
    pal_mod_settings.set_enabled(instance["serverPath"], package_name, enabled)


def _remove_tree(path: Path) -> bool:
    if not path.exists():
        return False
    shutil.rmtree(path)
    return True


def remove(instance: dict[str, Any], mod: dict[str, Any]) -> None:
    """Completely remove a Workshop mod from the selected server and all EGM caches."""
    workshop_id = parse_workshop_id(str(mod.get("workshopId") or ""))
    package_name = str(mod.get("packageName") or "").strip()
    source = instance.get("name") or "Workshop"

    if not package_name:
        try:
            package_name = inspect_installed(instance["serverPath"], workshop_id)["packageName"]
        except WorkshopError:
            package_name = ""

    if package_name:
        pal_mod_settings.set_enabled(instance["serverPath"], package_name, False)

    server_root = Path(instance["serverPath"]).resolve()
    paths: list[Path] = [
        workshop_root(server_root) / workshop_id,
        server_root / "steamapps" / "workshop" / "content" / PALWORLD_APP_ID / workshop_id,
        server_root / "steamapps" / "workshop" / "downloads" / PALWORLD_APP_ID / workshop_id,
        server_root.parent / "steamapps" / "workshop" / "content" / PALWORLD_APP_ID / workshop_id,
        server_root.parent / "steamapps" / "workshop" / "downloads" / PALWORLD_APP_ID / workshop_id,
        steamcmd.STEAMCMD_DIR / "steamapps" / "workshop" / "content" / PALWORLD_APP_ID / workshop_id,
        steamcmd.STEAMCMD_DIR / "steamapps" / "workshop" / "downloads" / PALWORLD_APP_ID / workshop_id,
    ]
    if package_name:
        paths.append(server_root / "Mods" / "ManagedMods" / package_name)

    deleted: list[str] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        if _remove_tree(path):
            deleted.append(str(path))

    activity_log.log(
        "info",
        source,
        f"Workshop mod {package_name or workshop_id} removed completely ({len(deleted)} folder(s) deleted).",
    )

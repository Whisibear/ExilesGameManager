"""Nexus-download orchestration for mod installs - selecting a downloadable
file from a Nexus mod's file list, downloading it, and installing it into
the right mods folder. Used by both the direct "install from Nexus" route
and Mod Wishlist approval."""

import hashlib
import json
import logging
import re
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import httpx
import py7zr
from fastapi import HTTPException

from app import paths
from app.services import (
    activity_log,
    local_config,
    mod_installer,
    mods_shared,
    mods_store,
    nexus_client,
    nexus_session,
    nexus_inventory,
    pal_mod_settings,
    process_manager,
)
from app.services.mod_installer import ModInstallError
from app.services.nexus_client import NexusApiError

logger = logging.getLogger("egm.mods")

NEXUS_DOWNLOAD_DIR = paths.downloads_dir() / "nexus"
NEXUS_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def with_update_status(mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Populates real updateAvailable/latestVersion (previously always false/
    unset) via a single keyless GraphQL lookup, computed per-request rather
    than persisted so it always reflects Nexus's current published version.
    Also flags manually-installed mods - verified file uploads (`verified-`
    id prefix) and mods discovered already sitting on disk instead of
    installed through this app (`manuallyInstalled` already set true by
    `mods_shared.register_untracked_disk_mods`) - since their sourceModId (if
    any) only proves a hash match with something on Nexus, not that they
    came through the Nexus download/wishlist pipeline "Request Update"
    triggers, so they're excluded from the update check entirely."""
    mods = [
        {**m, "manuallyInstalled": m["id"].startswith("verified-") or m.get("manuallyInstalled", False)} for m in mods
    ]
    mod_ids = [m["sourceModId"] for m in mods if m.get("sourceModId") and not m["manuallyInstalled"]]
    if not mod_ids:
        return mods
    try:
        current_versions = await nexus_client.get_current_versions(mod_ids)
    except NexusApiError as e:
        logger.info("mods: skipping update check (%s)", e.message)
        return mods

    result = []
    for m in mods:
        current = current_versions.get(m.get("sourceModId"))
        if current and current != m.get("version"):
            m = {**m, "updateAvailable": True, "latestVersion": current}
        result.append(m)
    return result



async def check_updates(instance: dict[str, Any]) -> dict[str, Any]:
    mods = mods_store.load_mods(instance["id"])
    nexus_mods = [m for m in mods if m.get("sourceModId") and not m.get("workshopId") and not m.get("manuallyInstalled")]
    source = instance.get("name") or "Nexus Mods"
    activity_log.log("info", source, f"Checking {len(nexus_mods)} Nexus mod(s) for updates.")
    enriched_all = await with_update_status(mods)
    by_id = {str(m.get("id")): m for m in enriched_all}
    results = [by_id[str(m.get("id"))] for m in nexus_mods if str(m.get("id")) in by_id]
    updates = sum(1 for m in results if m.get("updateAvailable"))
    for mod in results:
        state = "update available" if mod.get("updateAvailable") else "up to date"
        activity_log.log("info", source, f"Nexus mod {mod.get('name') or mod.get('sourceModId')}: {state}.")
    activity_log.log("info", source, f"Nexus mod update check completed: {updates} update(s) available.")
    return {"checked": len(results), "updatesAvailable": updates, "upToDate": updates == 0, "mods": results}

def is_main_file(file_info: dict[str, Any]) -> bool:
    category_id = file_info.get("category_id")
    category_name = str(file_info.get("category_name") or "").lower()
    return category_id == 1 or "main" in category_name


def installable_nexus_files(files_payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Current (non-old-version) files, Main file(s) first then newest-first -
    same candidate set/ordering `_select_installable_nexus_file` used to pick
    a single winner from, now exposed so a mod with more than one current
    file (e.g. Main + Optional Files) can be shown as real choices instead of
    only ever installing whichever one sorts first."""
    files = files_payload.get("files") or []
    if not files:
        raise HTTPException(status_code=404, detail="Nexus returned no downloadable files for this mod.")

    candidates = [f for f in files if not f.get("is_old_version")]
    if not candidates:
        candidates = files
    return sorted(candidates, key=lambda f: (not is_main_file(f), -(f.get("uploaded_timestamp") or 0)))


def _select_installable_nexus_file(files_payload: dict[str, Any], file_id: int | None = None) -> dict[str, Any]:
    candidates = installable_nexus_files(files_payload)
    if file_id is None:
        return candidates[0]
    for f in files_payload.get("files") or []:
        if int(f.get("file_id", -1)) == file_id:
            return f
    raise HTTPException(status_code=404, detail="That file is no longer available for this mod on Nexus.")


def _download_link_url(links: list[dict[str, Any]]) -> str:
    for link in links:
        url = link.get("URI") or link.get("uri")
        if url:
            return str(url)
    raise HTTPException(status_code=502, detail="Nexus did not return a usable download mirror.")


def _safe_download_name(name: str, fallback: str) -> str:
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in " ._-").strip()
    return cleaned or fallback


_NEXUS_MARKER = ".egm-nexus.json"
_PACKAGE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _extract_for_inspection(archive_path: Path, destination: Path) -> None:
    mod_installer._safe_extract_archive(archive_path, destination)


def _find_info_json(root: Path) -> Path | None:
    files = sorted(
        root.rglob("Info.json"),
        key=lambda path: (len(path.relative_to(root).parts), str(path).lower()),
    )
    return files[0] if files else None


def _read_palmod_package(root: Path) -> dict[str, Any] | None:
    info_path = _find_info_json(root)
    if info_path is None:
        return None
    try:
        payload = json.loads(info_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"Nexus mod contains an invalid Info.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Nexus mod Info.json must contain a JSON object.")
    package_name = str(payload.get("PackageName") or "").strip()
    if not package_name or not _PACKAGE_NAME_RE.fullmatch(package_name):
        raise HTTPException(status_code=422, detail="Nexus mod Info.json contains no valid PackageName.")
    raw_rules = payload.get("InstallRules")
    rules = [raw_rules] if isinstance(raw_rules, dict) else [
        item for item in raw_rules if isinstance(item, dict)
    ] if isinstance(raw_rules, list) else []
    if rules and not any(rule.get("IsServer") is True for rule in rules):
        raise HTTPException(
            status_code=422,
            detail="This Nexus mod package is not marked for dedicated servers (InstallRules IsServer=true).",
        )
    return {"packageName": package_name, "sourceDir": info_path.parent, "info": payload}


def _workshop_folder_name(mod_id: int, file_id: int) -> str:
    return f"Nexus-{mod_id}-{file_id}"


def _write_marker(folder: Path, metadata: dict[str, Any]) -> None:
    (folder / _NEXUS_MARKER).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_marker(folder: Path) -> dict[str, Any] | None:
    path = folder / _NEXUS_MARKER
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _deployment_paths(server_path: str | Path, package_name: str) -> list[Path]:
    server = Path(server_path)
    return [
        server / "Mods" / "ManagedMods" / package_name,
        server / "Mods" / "NativeMods" / "UE4SS" / "Mods" / package_name,
        server / "Mods" / "NativeMods" / "UE4SS" / "Mods" / "PalSchema" / "mods" / package_name,
        server / "Pal" / "Content" / "Paks" / "LogicMods" / package_name,
        server / "Pal" / "Content" / "Paks" / "~WorkshopMods" / package_name,
    ]


def _deployed_path(server_path: str | Path, package_name: str) -> Path | None:
    if not package_name:
        return None
    return next((path for path in _deployment_paths(server_path, package_name) if path.exists()), None)


def _install_official_package(
    instance: dict[str, Any],
    package: dict[str, Any],
    mod_id: int,
    file_id: int,
    archive: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    folder_name = _workshop_folder_name(mod_id, file_id)
    destination = pal_mod_settings.workshop_root(instance["serverPath"]) / folder_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    rollback = destination.with_name(f".{destination.name}.rollback")
    if rollback.exists():
        shutil.rmtree(rollback, ignore_errors=True)
    try:
        if destination.exists():
            destination.rename(rollback)
        shutil.copytree(Path(package["sourceDir"]), destination)
        _write_marker(
            destination,
            {
                "source": "nexus",
                "nexusModId": mod_id,
                "nexusFileId": file_id,
                "packageName": package["packageName"],
                "archive": str(archive),
                "installedAt": int(time.time()),
                **metadata,
            },
        )
        pal_mod_settings.set_enabled(instance["serverPath"], package["packageName"], True)
        if rollback.exists():
            shutil.rmtree(rollback, ignore_errors=True)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        if rollback.exists():
            rollback.rename(destination)
        raise
    deployed = _deployed_path(instance["serverPath"], package["packageName"])
    return {
        "installKind": "palmod_nexus",
        "folderName": folder_name,
        "packageName": package["packageName"],
        "sourcePath": str(destination),
        "deployedPath": str(deployed) if deployed else None,
        "deploymentStatus": "deployed" if deployed else "configured",
        "deploymentMessage": (
            "Deployed by Palworld."
            if deployed
            else "Configured in PalModSettings.ini. Manual server restart required."
        ),
    }



_PAK_TARGET_SEGMENTS = {
    "logicmods": "logicmods",
    "~workshopmods": "workshop_pak",
    "~mods": "pak",
}
_PAK_SIDE_SUFFIXES = {".pak", ".utoc", ".ucas", ".sig"}
_STRUCTURAL_NAMES = {
    "pal",
    "palworld",
    "content",
    "paks",
    "~mods",
    "~workshopmods",
    "logicmods",
    "mods",
}
_PROTECTED_PAK_NAMES = {
    "pal-windowsserver.pak",
    "pal-windows.pak",
}


def _normalized_archive_parts(name: str) -> list[str]:
    return [part for part in name.replace("\\", "/").split("/") if part]


def _detect_pak_archive_layout(archive: Path) -> dict[str, Any] | None:
    names = mod_installer._archive_names(archive)
    pak_names = [name for name in names if Path(name).suffix.lower() == ".pak"]
    if not pak_names:
        return None

    best: dict[str, Any] | None = None
    for original in pak_names:
        parts = _normalized_archive_parts(original)
        lowered = [part.lower() for part in parts]
        candidates = [
            (index, _PAK_TARGET_SEGMENTS[part], part)
            for index, part in enumerate(lowered)
            if part in _PAK_TARGET_SEGMENTS
        ]
        if not candidates:
            continue

        # The deepest target segment is authoritative. This fixes malformed
        # archives such as Paks/~mods/LogicMods/Example.pak.
        index, kind, segment = max(candidates, key=lambda item: item[0])
        candidate = {
            "kind": kind,
            "prefix": "/".join(parts[: index + 1]) + "/",
            "segment": parts[index],
            "depth": index,
        }
        if best is None or candidate["depth"] > best["depth"]:
            best = candidate

    if best:
        best.pop("depth", None)
        return best
    return {"kind": "pak", "prefix": "", "segment": "~mods"}


def _pak_destination(instance: dict[str, Any], kind: str) -> Path:
    server_path = instance.get("serverPath")
    if not server_path:
        raise HTTPException(status_code=400, detail="No server path configured.")
    paks_root = local_config.pal_directory(server_path) / "Content" / "Paks"
    if kind == "logicmods":
        return paks_root / "LogicMods"
    if kind == "workshop_pak":
        return paks_root / "~WorkshopMods"
    return paks_root / "~mods"


def _descend_structural_wrappers(path: Path) -> Path:
    current = path
    while current.is_dir():
        entries = [entry for entry in current.iterdir() if entry.name not in {"__MACOSX"}]
        if len(entries) != 1 or not entries[0].is_dir():
            break
        if entries[0].name.lower() not in _STRUCTURAL_NAMES:
            break
        current = entries[0]
    return current


def _copy_pak_payload(
    archive: Path,
    destination: Path,
    fallback_name: str,
    prefix: str,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="egm-nexus-pak-") as temp_name:
        extracted = Path(temp_name)
        mod_installer._safe_extract_archive(archive, extracted)

        payload_root = extracted
        for segment in prefix.strip("/").split("/") if prefix else []:
            payload_root = payload_root / segment
        payload_root = _descend_structural_wrappers(payload_root)

        if not payload_root.is_dir():
            raise HTTPException(status_code=422, detail="The Nexus archive contains an invalid PAK directory layout.")

        files = [
            file
            for file in payload_root.rglob("*")
            if file.is_file() and file.suffix.lower() in _PAK_SIDE_SUFFIXES
        ]
        if not files:
            raise HTTPException(status_code=422, detail="The Nexus archive contains no installable PAK files.")

        top_level = {file.relative_to(payload_root).parts[0] for file in files}
        preserve_top_folder = (
            len(top_level) == 1
            and (payload_root / next(iter(top_level))).is_dir()
            and next(iter(top_level)).lower() not in _STRUCTURAL_NAMES
        )
        safe_name = mod_installer._sanitize_name(fallback_name)
        installed_paths: list[str] = []

        for source in files:
            relative = source.relative_to(payload_root)
            if preserve_top_folder:
                target = destination / relative
            elif len(relative.parts) > 1 and relative.parts[0].lower() not in _STRUCTURAL_NAMES:
                target = destination / relative
            else:
                target = destination / source.name

            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target.unlink()
            shutil.copy2(source, target)
            installed_paths.append(str(target))

        if preserve_top_folder:
            folder_name = next(iter(top_level))
            deployed_path = destination / folder_name
        else:
            primary_pak = next(file for file in files if file.suffix.lower() == ".pak")
            folder_name = primary_pak.stem or safe_name
            deployed_path = destination / primary_pak.name

    return {
        "folderName": folder_name,
        "installedPaths": installed_paths,
        "deployedPath": str(deployed_path),
        "installRoot": str(destination),
    }


def _pak_scan_roots(instance: dict[str, Any]) -> list[tuple[str, Path]]:
    server_path = instance.get("serverPath")
    if not server_path:
        return []
    paks = local_config.pal_directory(server_path) / "Content" / "Paks"
    return [
        ("pak", paks / "~mods"),
        ("logicmods", paks / "LogicMods"),
        ("workshop_pak", paks / "~WorkshopMods"),
    ]


def _move_payload(source: Path, destination: Path) -> list[Path]:
    moved: list[Path] = []
    destination.mkdir(parents=True, exist_ok=True)
    for entry in list(source.iterdir()):
        target = destination / entry.name
        if target.exists():
            if entry.is_file() and target.is_file():
                if hashlib.sha256(entry.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest():
                    entry.unlink()
                    continue
                target = destination / f"{entry.stem}-migrated{entry.suffix}"
            elif entry.is_dir() and target.is_dir():
                moved.extend(_move_payload(entry, target))
                if entry.exists() and not any(entry.iterdir()):
                    entry.rmdir()
                continue
            else:
                target = destination / f"{entry.name}-migrated"
        shutil.move(str(entry), str(target))
        moved.append(target)
    return moved


def _prune_empty_parents(path: Path, stop: Path) -> None:
    current = path
    while current != stop and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _migrate_legacy_pak_layouts(instance: dict[str, Any]) -> list[str]:
    """Repair layouts produced by earlier EGM beta builds without touching
    Palworld's base PAK. Only known wrapper paths inside mod roots are moved."""
    server_path = instance.get("serverPath")
    if not server_path:
        return []

    paks_root = local_config.pal_directory(server_path) / "Content" / "Paks"
    migrations: list[str] = []
    source_roots = [paks_root / "~mods", paks_root / "~WorkshopMods", paks_root / "LogicMods"]

    # Direct malformed nesting: ~mods/LogicMods/*.pak
    nested_logic = paks_root / "~mods" / "LogicMods"
    if nested_logic.is_dir():
        moved = _move_payload(nested_logic, paks_root / "LogicMods")
        migrations.extend(f"{path}" for path in moved)
        _prune_empty_parents(nested_logic, paks_root / "~mods")

    # Full game-root wrappers accidentally copied below a mod destination.
    for scan_root in source_roots:
        if not scan_root.is_dir():
            continue
        for nested_paks in list(scan_root.rglob("Paks")):
            if not nested_paks.is_dir() or nested_paks == paks_root:
                continue
            for segment, kind in _PAK_TARGET_SEGMENTS.items():
                nested_target = nested_paks / (
                    "LogicMods" if segment == "logicmods"
                    else "~WorkshopMods" if segment == "~workshopmods"
                    else "~mods"
                )
                if nested_target.is_dir():
                    moved = _move_payload(nested_target, _pak_destination(instance, kind))
                    migrations.extend(f"{path}" for path in moved)
                    _prune_empty_parents(nested_target, scan_root)

    if migrations:
        logger.warning(
            "Migrated malformed Nexus PAK layout instance=%s files=%s",
            instance.get("id"),
            migrations,
        )
        activity_log.log(
            "warning",
            instance.get("name") or "Nexus Mods",
            f"Repaired {len(migrations)} Nexus PAK file path(s) created by an older EGM beta.",
            instance_id=instance.get("id"),
        )
    return migrations


def _payload_group_key(root: Path, file: Path) -> tuple[str, Path]:
    relative = file.relative_to(root)
    if len(relative.parts) > 1 and relative.parts[0].lower() not in _STRUCTURAL_NAMES:
        return relative.parts[0], root / relative.parts[0]
    return file.stem, file


def _existing_record_for_paths(
    mods: list[dict[str, Any]],
    kind: str,
    paths: list[Path],
    display_name: str,
) -> dict[str, Any] | None:
    normalized_paths = {str(path.resolve()).lower() for path in paths}
    normalized_name = re.sub(r"[^a-z0-9]+", "", display_name.lower())
    for mod in mods:
        if not _is_nexus_mod(mod):
            continue
        record_paths = {
            str(Path(str(value)).resolve()).lower()
            for value in [
                mod.get("deployedPath"),
                *(mod.get("installedPaths") or []),
            ]
            if value
        }
        if normalized_paths & record_paths:
            return mod
        mod_name = re.sub(r"[^a-z0-9]+", "", str(mod.get("name") or "").lower())
        if mod_name and mod_name == normalized_name and str(mod.get("installKind") or "") in {
            kind,
            "pak",
            "logicmods",
            "workshop_pak",
        }:
            return mod
    return None


def _recover_pak_nexus_mods(instance: dict[str, Any], mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _migrate_legacy_pak_layouts(instance)
    changed = False

    for kind, root in _pak_scan_roots(instance):
        if not root.is_dir():
            continue

        pak_files = [
            file
            for file in root.rglob("*")
            if file.is_file()
            and file.suffix.lower() == ".pak"
            and file.name.lower() not in _PROTECTED_PAK_NAMES
        ]
        grouped: dict[str, dict[str, Any]] = {}
        for pak_file in pak_files:
            display_name, deployed = _payload_group_key(root, pak_file)
            group = grouped.setdefault(
                str(deployed.resolve()).lower(),
                {"name": display_name, "deployed": deployed, "files": []},
            )
            stem = pak_file.stem.lower()
            siblings = [
                path
                for path in pak_file.parent.iterdir()
                if path.is_file()
                and path.stem.lower() == stem
                and path.suffix.lower() in _PAK_SIDE_SUFFIXES
            ]
            for sibling in siblings:
                if sibling not in group["files"]:
                    group["files"].append(sibling)

        for group in grouped.values():
            existing = _existing_record_for_paths(mods, kind, group["files"], group["name"])
            if existing:
                existing.update(
                    {
                        "folderName": group["name"],
                        "installKind": kind,
                        "deployedPath": str(group["deployed"]),
                        "installedPaths": [str(path) for path in group["files"]],
                        "deploymentStatus": "deployed",
                        "deploymentMessage": f"Installed in Pal/Content/Paks/{root.name}.",
                        "status": "enabled",
                    }
                )
                changed = True
                continue

            mods.append(
                {
                    "id": mods_store.new_id("nexus"),
                    "name": group["name"],
                    "version": "Unknown",
                    "author": "Unknown",
                    "description": f"Detected in {root.name}.",
                    "dependencies": [],
                    "status": "enabled",
                    "loadPriority": len(mods) + 1,
                    "updateAvailable": False,
                    "source": "nexus",
                    "sourceModId": None,
                    "nexusModId": None,
                    "nexusFileId": None,
                    "previewUrl": None,
                    "nexusUrl": None,
                    "downloadedFile": None,
                    "folderName": group["name"],
                    "packageName": None,
                    "installKind": kind,
                    "sourcePath": None,
                    "deployedPath": str(group["deployed"]),
                    "installedPaths": [str(path) for path in group["files"]],
                    "deploymentStatus": "deployed",
                    "deploymentMessage": f"Detected in Pal/Content/Paks/{root.name}.",
                    "recoveredFromDisk": True,
                }
            )
            changed = True

    if changed:
        mods_store.save_mods(instance["id"], mods)
    return mods

def _install_legacy_archive(instance: dict[str, Any], archive: Path, mod_name: str) -> dict[str, Any]:
    layout = _detect_pak_archive_layout(archive)
    if layout:
        destination = _pak_destination(instance, layout["kind"])
        installed = _copy_pak_payload(archive, destination, mod_name, layout["prefix"])
        return {
            "installKind": layout["kind"],
            "folderName": installed["folderName"],
            "packageName": None,
            "sourcePath": None,
            "deployedPath": installed["deployedPath"],
            "installedPaths": installed["installedPaths"],
            "installRoot": installed["installRoot"],
            "deploymentStatus": "deployed",
            "deploymentMessage": f"Installed in Pal/Content/Paks/{destination.name}.",
        }

    kind = mod_installer.detect_mod_kind(archive)
    install_path = mods_shared.base_path_for_kind(instance, kind)
    if not install_path:
        raise HTTPException(status_code=400, detail="No Mods folder configured for this server yet.")
    folder_name = mod_installer.extract_and_install(archive, Path(install_path), mod_name)
    target = Path(install_path) / folder_name
    if kind == "ue4ss":
        _set_ue4ss_mod_enabled(instance, folder_name, True)
    return {
        "installKind": kind,
        "folderName": folder_name,
        "packageName": None,
        "sourcePath": None,
        "deployedPath": str(target),
        "installedPaths": [str(target)],
        "installRoot": str(Path(install_path)),
        "deploymentStatus": "deployed",
        "deploymentMessage": "Installed in the UE4SS Mods directory.",
    }


def _recover_marked_packages(instance: dict[str, Any], mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    server_path = instance.get("serverPath")
    if not server_path:
        return mods
    tracked = {
        str(Path(str(mod.get("sourcePath"))).resolve()).lower()
        for mod in mods
        if mod.get("sourcePath")
    }
    root = pal_mod_settings.workshop_root(server_path)
    if not root.is_dir():
        return mods
    active = set(pal_mod_settings.active_mods(server_path))
    changed = False
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        marker = _read_marker(folder)
        if not marker or str(folder.resolve()).lower() in tracked:
            continue
        package_name = str(marker.get("packageName") or "").strip()
        deployed = _deployed_path(server_path, package_name)
        mods.append(
            {
                "id": mods_store.new_id("nexus"),
                "name": marker.get("name") or package_name or folder.name,
                "version": marker.get("version") or "Unknown",
                "author": marker.get("author") or "Unknown",
                "description": marker.get("description") or "",
                "dependencies": [],
                "status": "enabled" if package_name in active else "disabled",
                "loadPriority": len(mods) + 1,
                "updateAvailable": False,
                "source": "nexus",
                "sourceModId": marker.get("nexusModId"),
                "nexusModId": marker.get("nexusModId"),
                "nexusFileId": marker.get("nexusFileId"),
                "previewUrl": marker.get("previewUrl"),
                "nexusUrl": marker.get("nexusUrl"),
                "downloadedFile": marker.get("archive"),
                "folderName": folder.name,
                "packageName": package_name or None,
                "installKind": "palmod_nexus",
                "sourcePath": str(folder),
                "deployedPath": str(deployed) if deployed else None,
                "deploymentStatus": "deployed" if deployed else "configured",
                "deploymentMessage": (
                    "Deployed by Palworld."
                    if deployed
                    else "Configured in PalModSettings.ini. Manual server restart required."
                ),
            }
        )
        changed = True
    if changed:
        mods_store.save_mods(instance["id"], mods)
    return mods


_RICH_METADATA_FIELDS = ("name", "version", "author", "description", "previewUrl", "nexusUrl", "sourceModId", "nexusModId", "nexusFileId")


def _has_rich_nexus_metadata(mod: dict[str, Any]) -> bool:
    return bool(int(mod.get("nexusModId") or mod.get("sourceModId") or 0) and str(mod.get("name") or "").strip() and str(mod.get("name") or "").lower() not in {"unknown", "nexus mod"})


def _merge_rich_metadata(target: dict[str, Any], source: dict[str, Any] | None) -> dict[str, Any]:
    if not source:
        return target
    merged = dict(target)
    for field in _RICH_METADATA_FIELDS:
        value = source.get(field)
        if value not in (None, "", 0, "Unknown"):
            merged[field] = value
    for field in ("installedAt", "updatedAt", "runtimeVerification"):
        if source.get(field) is not None:
            merged[field] = source[field]
    return merged


def _record_paths(mod: dict[str, Any]) -> set[str]:
    values = [mod.get("sourcePath"), mod.get("deployedPath"), *(mod.get("installedPaths") or [])]
    return {str(Path(str(value)).resolve()).lower() for value in values if value}


def _deduplicate_nexus_records(instance_id: str, mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for record in mods:
        if not _is_nexus_mod(record):
            result.append(record)
            continue
        metadata = nexus_inventory.find_match(instance_id, record)
        record = _merge_rich_metadata(record, metadata)
        record_paths = _record_paths(record)
        normalized_name = re.sub(r"[^a-z0-9]+", "", str(record.get("name") or "").lower())
        match_index = None
        for index, current in enumerate(result):
            if not _is_nexus_mod(current):
                continue
            current_paths = _record_paths(current)
            record_id = int(record.get("nexusModId") or record.get("sourceModId") or 0)
            current_id = int(current.get("nexusModId") or current.get("sourceModId") or 0)
            current_name = re.sub(r"[^a-z0-9]+", "", str(current.get("name") or "").lower())
            if (record_id and record_id == current_id) or (record_paths and record_paths & current_paths) or (normalized_name and normalized_name == current_name and str(record.get("installKind") or "") == str(current.get("installKind") or "")):
                match_index = index
                break
        if match_index is None:
            result.append(record)
            continue
        current = result[match_index]
        preferred = current if _has_rich_nexus_metadata(current) else record
        secondary = record if preferred is current else current
        merged = dict(secondary)
        merged.update(preferred)
        merged = _merge_rich_metadata(merged, metadata)
        merged["installedPaths"] = sorted({str(path) for path in [*(current.get("installedPaths") or []), *(record.get("installedPaths") or [])] if path})
        result[match_index] = merged
    for record in result:
        if _is_nexus_mod(record) and _has_rich_nexus_metadata(record):
            nexus_inventory.upsert(instance_id, record)
    return result


async def install_nexus_mod(
    instance: dict[str, Any], nexus_mod_id: int, file_id: int | None = None
) -> list[dict[str, Any]]:
    access_token = await nexus_session.require_premium_access_token()
    mods_path = local_config.get_mods_path(instance)
    if not mods_path:
        raise HTTPException(status_code=400, detail="No Mods folder configured for this server yet.")

    try:
        details = await nexus_client.get_mod_details(access_token, nexus_mod_id)
        files_payload = await nexus_client.get_mod_files(access_token, nexus_mod_id)
        file_info = _select_installable_nexus_file(files_payload, file_id)
        file_id = int(file_info["file_id"])
        links = await nexus_client.get_download_link(access_token, nexus_mod_id, file_id)
    except NexusApiError as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=502, detail="Nexus returned an unexpected file response.")

    file_name = _safe_download_name(
        str(file_info.get("file_name") or file_info.get("name") or ""),
        f"nexus-{nexus_mod_id}-{file_id}.zip",
    )
    if "." not in file_name:
        # Only guess an extension when the real name didn't have one at all -
        # forcing ".zip" unconditionally used to mislabel real .7z downloads.
        file_name = f"{file_name}.zip"
    dest = NEXUS_DOWNLOAD_DIR / f"{nexus_mod_id}-{file_id}-{file_name}"

    try:
        await nexus_client.download_file(_download_link_url(links), dest)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Nexus file download failed.")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Nexus file download failed: {e}")

    if not mod_installer.is_supported_archive(dest):
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422, detail="The downloaded Nexus file is not a supported archive (.zip or .7z)."
        )

    mod_name = details.get("name") or file_info.get("name") or "Nexus Mod"
    metadata = {
        "name": mod_name,
        "version": file_info.get("version") or details.get("version") or "See Nexus",
        "author": details.get("author") or "Unknown",
        "description": details.get("summary") or details.get("description") or "",
        "previewUrl": details.get("picture_url") or details.get("pictureUrl"),
        "nexusUrl": f"https://www.nexusmods.com/{nexus_client.GAME_DOMAIN}/mods/{nexus_mod_id}",
    }
    try:
        with tempfile.TemporaryDirectory(prefix="egm-nexus-") as tmp:
            extracted = Path(tmp)
            _extract_for_inspection(dest, extracted)
            package = _read_palmod_package(extracted)
            placement = (
                _install_official_package(instance, package, nexus_mod_id, file_id, dest, metadata)
                if package
                else _install_legacy_archive(instance, dest, mod_name)
            )
    except (zipfile.BadZipFile, py7zr.exceptions.ArchiveError):
        raise HTTPException(status_code=422, detail="The downloaded Nexus file is not a valid archive.")
    except ModInstallError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except HTTPException:
        raise
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Couldn't place mod files on disk: {e}")

    mods = mods_store.load_mods(instance["id"])
    existing = next((m for m in mods if m.get("sourceModId") == nexus_mod_id), None)
    entry = {
        "id": existing["id"] if existing else mods_store.new_id("nexus"),
        "name": mod_name,
        "version": metadata["version"],
        "author": metadata["author"],
        "description": metadata["description"],
        "dependencies": existing.get("dependencies", []) if existing else [],
        "status": "enabled",
        "loadPriority": existing["loadPriority"] if existing else len(mods) + 1,
        "updateAvailable": False,
        "source": "nexus",
        "sourceModId": nexus_mod_id,
        "nexusModId": nexus_mod_id,
        "nexusFileId": file_id,
        "previewUrl": metadata["previewUrl"],
        "nexusUrl": metadata["nexusUrl"],
        "downloadedFile": str(dest),
        **placement,
    }
    if existing:
        mods = [entry if m["id"] == existing["id"] else m for m in mods]
    else:
        mods.append(entry)
    mods_store.save_mods(instance["id"], mods)
    nexus_inventory.upsert(instance["id"], entry)
    activity_log.log(
        "info",
        instance.get("name") or "Nexus Mods",
        (
            f"Nexus mod installed: {entry['name']} (Nexus {nexus_mod_id}, file {file_id}). "
            f"Mode: {entry['installKind']}. {entry.get('deploymentMessage') or ''}"
        ),
        instance_id=instance["id"],
    )
    logger.info(
        "Nexus install completed instance=%s mod_id=%s file_id=%s mode=%s package=%s folder=%s",
        instance["id"], nexus_mod_id, file_id, entry.get("installKind"),
        entry.get("packageName"), entry.get("folderName"),
    )
    return await with_update_status(mods_store.sorted_mods(mods))



def _is_nexus_mod(mod: dict[str, Any]) -> bool:
    return bool(
        mod.get("source") == "nexus"
        or mod.get("sourceModId")
        or mod.get("nexusModId")
        or str(mod.get("id") or "").startswith("nexus-")
    )


def _inventory_from_mods(instance: dict[str, Any], mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    server_path = instance.get("serverPath")
    active = set(pal_mod_settings.active_mods(server_path)) if server_path else set()
    ue4ss_states = _read_ue4ss_mod_states(instance)

    for mod in mods_store.sorted_mods(mods):
        if not _is_nexus_mod(mod):
            continue

        kind = str(mod.get("installKind") or "ue4ss")
        folder_name = str(mod.get("folderName") or "")
        package_name = str(mod.get("packageName") or "").strip() or None
        archive = Path(str(mod.get("downloadedFile") or "")) if mod.get("downloadedFile") else None
        recorded_paths = [
            Path(str(path))
            for path in mod.get("installedPaths") or []
            if path
        ]

        source: Path | None = None
        installed_path: Path | None = None
        deployed: Path | None = None
        configured = False

        if kind == "palmod_nexus" and server_path:
            source = Path(str(mod.get("sourcePath"))) if mod.get("sourcePath") else (
                pal_mod_settings.workshop_root(server_path) / folder_name
            )
            configured = bool(
                source.is_dir()
                and (source / "Info.json").is_file()
                and package_name
                and package_name in active
            )
            deployed = _deployed_path(server_path, package_name or "")
            installed_path = deployed or source
            status = (
                "installed" if deployed
                else "configured" if configured
                else "downloaded" if source.is_dir()
                else "missing"
            )
        else:
            if recorded_paths:
                existing_paths = [path for path in recorded_paths if path.exists()]
                deployed = Path(str(mod.get("deployedPath"))) if mod.get("deployedPath") else (
                    existing_paths[0] if existing_paths else None
                )
                installed_path = deployed
                status = "installed" if existing_paths else "downloaded" if archive and archive.is_file() else "missing"
            else:
                if kind in {"pak", "logicmods", "workshop_pak"} and server_path:
                    base_path = _pak_destination(instance, kind)
                else:
                    base_value = mods_shared.base_path_for_kind(instance, kind)
                    base_path = Path(base_value) if base_value else None
                installed_path = base_path / folder_name if base_path and folder_name else None
                deployed = installed_path if installed_path and installed_path.exists() else None
                status = "installed" if deployed else "downloaded" if archive and archive.is_file() else "missing"

            if kind == "ue4ss" and folder_name:
                mod["status"] = "enabled" if ue4ss_states.get(folder_name, True) else "disabled"

        archive_available = bool(archive and archive.is_file())
        result.append(
            {
                "id": str(mod["id"]),
                "modId": int(mod.get("sourceModId") or mod.get("nexusModId") or 0),
                "fileId": mod.get("nexusFileId"),
                "name": str(mod.get("name") or "Nexus Mod"),
                "author": str(mod.get("author") or "Unknown"),
                "version": str(mod.get("version") or "Unknown"),
                "description": str(mod.get("description") or ""),
                "previewUrl": mod.get("previewUrl"),
                "nexusUrl": mod.get("nexusUrl"),
                "status": status,
                "enabled": (
                    package_name in active
                    if kind == "palmod_nexus" and package_name
                    else ue4ss_states.get(folder_name, mod.get("status") == "enabled")
                    if kind == "ue4ss" and folder_name
                    else mod.get("status") == "enabled"
                ),
                "installKind": kind,
                "installMode": (
                    "PalMod package" if kind == "palmod_nexus"
                    else "UE4SS mod" if kind == "ue4ss"
                    else "LogicMods PAK" if kind == "logicmods"
                    else "Workshop PAK" if kind == "workshop_pak"
                    else "PAK mod"
                ),
                "packageName": package_name,
                "folderName": folder_name or None,
                "sourcePath": str(source) if source else None,
                "installedPath": str(installed_path) if installed_path else None,
                "installedPaths": [str(path) for path in recorded_paths],
                "deployedPath": str(deployed) if deployed else None,
                "configured": configured,
                "deploymentStatus": (
                    "deployed" if status == "installed"
                    else "configured" if status == "configured"
                    else status
                ),
                "deploymentMessage": mod.get("deploymentMessage"),
                "downloadedFile": str(archive) if archive else None,
                "archiveAvailable": archive_available,
                "sizeBytes": archive.stat().st_size if archive_available and archive else 0,
                "loadPriority": int(mod.get("loadPriority") or 0),
                "recoveredFromDisk": bool(mod.get("recoveredFromDisk")),
                "installedAt": mod.get("installedAt"),
                "runtimeVerification": mod.get("runtimeVerification"),
            }
        )
    return result


_UE4SS_BUILTIN_MODS = {
    "CheatManagerEnablerMod",
    "ConsoleCommandsMod",
    "ConsoleEnablerMod",
    "SplitScreenMod",
    "LineTraceMod",
    "BPML_GenericFunctions",
    "BPModLoaderMod",
    "Keybinds",
    "shared",
}
_UE4SS_MOD_LINE_RE = re.compile(r"^\s*([^;:#][^:]*)\s*:\s*([01])\s*$")


def _ue4ss_root(instance: dict[str, Any]) -> Path | None:
    server_path = instance.get("serverPath")
    if not server_path:
        return None

    configured_mods_path = local_config.get_mods_path(instance) if instance.get("id") else None
    if configured_mods_path:
        configured = Path(configured_mods_path)
        if configured.name.lower() == "mods":
            return configured.parent

    pal_dir = local_config.pal_directory(server_path)
    candidates = [
        pal_dir / "Binaries" / "Win64" / "ue4ss",
        pal_dir / "Binaries" / "Win64" / "UE4SS",
    ]
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def _ue4ss_mods_dir(instance: dict[str, Any]) -> Path | None:
    root = _ue4ss_root(instance)
    return root / "Mods" if root else None


def _read_ue4ss_mod_states(instance: dict[str, Any]) -> dict[str, bool]:
    mods_dir = _ue4ss_mods_dir(instance)
    if mods_dir is None:
        return {}

    states: dict[str, bool] = {}

    json_path = mods_dir / "mods.json"
    if json_path.is_file():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8-sig"))
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("mod_name") or "").strip()
                    if name:
                        states[name] = bool(item.get("mod_enabled"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Could not parse UE4SS mods.json at %s", json_path)

    txt_path = mods_dir / "mods.txt"
    if txt_path.is_file():
        try:
            for line in txt_path.read_text(encoding="utf-8-sig").splitlines():
                match = _UE4SS_MOD_LINE_RE.match(line)
                if match:
                    states[match.group(1).strip()] = match.group(2) == "1"
        except (OSError, UnicodeDecodeError):
            logger.warning("Could not parse UE4SS mods.txt at %s", txt_path)

    enabled_path = mods_dir / "enabled.txt"
    if enabled_path.is_file():
        try:
            for line in enabled_path.read_text(encoding="utf-8-sig").splitlines():
                name = line.strip()
                if name and not name.startswith((";", "#")):
                    states[name] = True
        except (OSError, UnicodeDecodeError):
            logger.warning("Could not parse UE4SS enabled.txt at %s", enabled_path)

    return states


def _write_ue4ss_mod_states(instance: dict[str, Any], states: dict[str, bool]) -> None:
    mods_dir = _ue4ss_mods_dir(instance)
    if mods_dir is None:
        raise HTTPException(status_code=400, detail="UE4SS Mods folder is not configured for this server.")
    mods_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(states.items(), key=lambda item: item[0].lower())
    json_payload = [
        {"mod_name": name, "mod_enabled": enabled}
        for name, enabled in ordered
    ]
    (mods_dir / "mods.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (mods_dir / "mods.txt").write_text(
        "\n".join(f"{name} : {1 if enabled else 0}" for name, enabled in ordered) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _set_ue4ss_mod_enabled(instance: dict[str, Any], mod_name: str, enabled: bool) -> None:
    states = _read_ue4ss_mod_states(instance)
    states[mod_name] = enabled
    _write_ue4ss_mod_states(instance, states)


def _remove_ue4ss_mod_state(instance: dict[str, Any], mod_name: str) -> None:
    states = _read_ue4ss_mod_states(instance)
    if mod_name in states:
        states.pop(mod_name, None)
        _write_ue4ss_mod_states(instance, states)


def _is_builtin_ue4ss_mod(name: str) -> bool:
    return name in _UE4SS_BUILTIN_MODS


def _tracked_nexus_folder_names(mods: list[dict[str, Any]]) -> set[str]:
    return {
        str(mod.get("folderName") or "").strip()
        for mod in mods
        if _is_nexus_mod(mod) and str(mod.get("installKind") or "") == "ue4ss"
    }


def _recover_ue4ss_nexus_mods(instance: dict[str, Any], mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mods_dir = _ue4ss_mods_dir(instance)
    if mods_dir is None or not mods_dir.is_dir():
        return mods

    tracked_names = _tracked_nexus_folder_names(mods)
    states = _read_ue4ss_mod_states(instance)
    changed = False

    for folder in sorted(mods_dir.iterdir(), key=lambda path: path.name.lower()):
        if not folder.is_dir():
            continue
        name = folder.name
        if _is_builtin_ue4ss_mod(name) or name in tracked_names:
            continue

        mods.append(
            {
                "id": mods_store.new_id("nexus"),
                "name": name,
                "version": "Unknown",
                "author": "Unknown",
                "description": "Detected in the UE4SS Mods directory.",
                "dependencies": [],
                "status": "enabled" if states.get(name, True) else "disabled",
                "loadPriority": len(mods) + 1,
                "updateAvailable": False,
                "source": "nexus",
                "sourceModId": None,
                "nexusModId": None,
                "nexusFileId": None,
                "previewUrl": None,
                "nexusUrl": None,
                "downloadedFile": None,
                "folderName": name,
                "packageName": None,
                "installKind": "ue4ss",
                "sourcePath": None,
                "deployedPath": str(folder),
                "deploymentStatus": "deployed",
                "deploymentMessage": "Detected in UE4SS Mods directory.",
                "recoveredFromDisk": True,
            }
        )
        changed = True

    if changed:
        mods_store.save_mods(instance["id"], mods)
    return mods
def downloaded_nexus_mods(instance: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Nexus mods from both PalMod and UE4SS installation locations."""
    mods = mods_store.load_mods(instance["id"])
    mods = _recover_marked_packages(instance, mods)
    mods = _recover_ue4ss_nexus_mods(instance, mods)
    mods = _recover_pak_nexus_mods(instance, mods)
    mods = _deduplicate_nexus_records(instance["id"], mods)
    mods_store.save_mods(instance["id"], mods)
    inventory = _inventory_from_mods(instance, mods)
    logger.info(
        "Nexus inventory rescanned instance=%s server_path=%s ue4ss_path=%s items=%d",
        instance["id"],
        instance.get("serverPath"),
        _ue4ss_mods_dir(instance),
        len(inventory),
    )
    return inventory


def _allowed_mod_roots(
    instance: dict[str, Any],
    extra_roots: list[Path] | None = None,
) -> list[Path]:
    roots = [path.resolve() for _, path in _pak_scan_roots(instance)]
    ue4ss = _ue4ss_mods_dir(instance)
    if ue4ss:
        roots.append(ue4ss.resolve())

    server_path = instance.get("serverPath")
    if server_path:
        server_root = local_config.server_root_directory(server_path)
        roots.extend(
            [
                pal_mod_settings.workshop_root(server_path).resolve(),
                (server_root / "Mods" / "ManagedMods").resolve(),
                (server_root / "Mods" / "NativeMods").resolve(),
            ]
        )

    for root in extra_roots or []:
        roots.append(root.resolve())

    unique: list[Path] = []
    for root in roots:
        if root not in unique:
            unique.append(root)
    return unique


def _is_within(path: Path, root: Path) -> bool:
    try:
        return path == root or root in path.parents
    except (OSError, RuntimeError):
        return False


def _validate_delete_path(
    instance: dict[str, Any],
    path: Path,
    extra_roots: list[Path] | None = None,
) -> Path:
    resolved = path.resolve()
    allowed_roots = _allowed_mod_roots(instance, extra_roots)
    if not any(_is_within(resolved, root) and resolved != root for root in allowed_roots):
        raise HTTPException(
            status_code=422,
            detail=f"Refusing to remove an unsafe Nexus mod path: {resolved}",
        )
    if resolved.name.lower() in _PROTECTED_PAK_NAMES:
        raise HTTPException(
            status_code=422,
            detail=f"Refusing to remove protected Palworld file: {resolved.name}",
        )
    return resolved


def _remove_exact_paths(
    instance: dict[str, Any],
    paths_to_remove: list[Path],
    extra_roots: list[Path] | None = None,
) -> None:
    validated = []
    for path in paths_to_remove:
        if path.exists():
            validated.append(_validate_delete_path(instance, path, extra_roots))

    for path in sorted(validated, key=lambda item: len(item.parts), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)

    for path in validated:
        for root in _allowed_mod_roots(instance, extra_roots):
            if _is_within(path.parent, root):
                _prune_empty_parents(path.parent, root)
                break


def uninstall_downloaded_nexus_mod(instance: dict[str, Any], mod_id: str) -> list[dict[str, Any]]:
    # Game PAKs are memory-mapped while Palworld is running. Deleting them
    # then either fails with WinError 32 or risks a partial uninstall.
    state = process_manager.get_status(instance["id"]).get("state")
    if state in {"online", "starting", "stopping"}:
        raise HTTPException(
            status_code=409,
            detail="Stop the selected Palworld server before uninstalling Nexus mods.",
        )

    mods = mods_store.load_mods(instance["id"])
    target = next((mod for mod in mods if str(mod.get("id")) == mod_id), None)
    if target is None or not _is_nexus_mod(target):
        # Rescan once to stabilize records created from disk before failing.
        _recover_pak_nexus_mods(instance, mods)
        _recover_ue4ss_nexus_mods(instance, mods)
        mods = mods_store.load_mods(instance["id"])
        target = next((mod for mod in mods if str(mod.get("id")) == mod_id), None)
    if target is None or not _is_nexus_mod(target):
        raise HTTPException(status_code=404, detail="Downloaded Nexus mod was not found. Rescan Nexus Mods and try again.")

    kind = str(target.get("installKind") or "ue4ss")
    folder_name = str(target.get("folderName") or "")
    package_name = str(target.get("packageName") or "").strip()
    server_path = instance.get("serverPath")

    paths_to_remove = [
        Path(str(path))
        for path in target.get("installedPaths") or []
        if path
    ]
    extra_roots: list[Path] = []

    if kind == "palmod_nexus" and server_path:
        if package_name:
            pal_mod_settings.set_enabled(server_path, package_name, False)
        source = Path(str(target.get("sourcePath"))) if target.get("sourcePath") else (
            pal_mod_settings.workshop_root(server_path) / folder_name
        )
        paths_to_remove.append(source)
        extra_roots.append(source.parent)
        if package_name:
            paths_to_remove.extend(_deployment_paths(server_path, package_name))
    elif not paths_to_remove:
        if kind in {"pak", "logicmods", "workshop_pak"}:
            deployed = target.get("deployedPath")
            if deployed:
                paths_to_remove.append(Path(str(deployed)))
            elif folder_name:
                paths_to_remove.append(_pak_destination(instance, kind) / folder_name)
        else:
            base = mods_shared.base_path_for_kind(instance, kind)
            if folder_name and base:
                base_path = Path(base)
                extra_roots.append(base_path)
                paths_to_remove.append(base_path / folder_name)

    try:
        _remove_exact_paths(instance, paths_to_remove, extra_roots)
        if kind == "ue4ss" and folder_name:
            _remove_ue4ss_mod_state(instance, folder_name)

        archive = Path(str(target.get("downloadedFile") or "")) if target.get("downloadedFile") else None
        if archive and archive.is_file():
            archive_resolved = archive.resolve()
            if _is_within(archive_resolved, NEXUS_DOWNLOAD_DIR.resolve()):
                archive.unlink()
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail="A Nexus mod file is still in use. Stop the Palworld server and close tools using the mod folder, then try again.",
        ) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not uninstall Nexus mod files: {exc}") from exc

    remaining = [mod for mod in mods if str(mod.get("id")) != mod_id]
    mods_store.save_mods(instance["id"], remaining)
    nexus_inventory.remove(instance["id"], mod_id=int(target.get("nexusModId") or target.get("sourceModId") or 0), record_id=str(target.get("id") or ""))
    activity_log.log(
        "warning",
        instance.get("name") or "Nexus Mods",
        (
            f"Nexus mod uninstalled: {target.get('name') or mod_id}. "
            f"Removed {len(paths_to_remove)} tracked installation path(s)."
        ),
        instance_id=instance["id"],
    )
    logger.info(
        "Nexus uninstall completed instance=%s mod=%s kind=%s paths=%s",
        instance["id"],
        target.get("name"),
        kind,
        [str(path) for path in paths_to_remove],
    )
    return _inventory_from_mods(instance, remaining)


from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services import activity_log, local_config, mods_store, nexus_inventory, pal_mod_settings, process_manager


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ue4ss_log(instance: dict[str, Any]) -> Path:
    return local_config.pal_directory(instance["serverPath"]) / "Binaries" / "Win64" / "ue4ss" / "UE4SS.log"


def _deployment_paths(instance: dict[str, Any], mod: dict[str, Any]) -> list[Path]:
    pal = local_config.pal_directory(instance["serverPath"])
    kind = str(mod.get("installKind") or "")
    folder = str(mod.get("folderName") or "")
    package = str(mod.get("packageName") or "")
    paths = [Path(str(raw)) for raw in mod.get("installedPaths") or [] if raw]
    if mod.get("deployedPath"):
        paths.append(Path(str(mod["deployedPath"])))
    if kind == "ue4ss" and folder:
        paths.append(pal / "Binaries" / "Win64" / "ue4ss" / "Mods" / folder)
    elif kind == "logicmods" and folder:
        paths.append(pal / "Content" / "Paks" / "LogicMods" / folder)
    elif kind == "pak" and folder:
        paths.append(pal / "Content" / "Paks" / "~mods" / folder)
    elif kind == "workshop_pak" and folder:
        paths.append(pal / "Content" / "Paks" / "~WorkshopMods" / folder)
    if package:
        root = pal_mod_settings._server_root(instance["serverPath"])
        paths.append(root / "Mods" / "ManagedMods" / package / "InstallManifest.json")
    unique, seen = [], set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def _ue4ss_mod_evidence(text: str, mod: dict[str, Any]) -> tuple[bool, bool, str]:
    lowered = text.lower()
    names = {str(mod.get("folderName") or "").lower(), str(mod.get("name") or "").lower()}
    names.discard("")
    error = any(token in lowered for token in ("fatal error", "unhandled exception", "unable to load mod", "failed to load"))
    explicit = any(name in lowered for name in names)
    ready = "loading mods from:" in lowered and "starting mods" in lowered
    if error:
        return False, True, "UE4SS reported a loader error; inspect UE4SS.log."
    if ready and explicit:
        return True, False, "UE4SS initialized and referenced this mod in UE4SS.log."
    if ready:
        return False, False, "UE4SS initialized, but this mod was not explicitly referenced in the available log."
    return False, False, "UE4SS startup evidence is unavailable."


def _verification_for_mod(instance: dict[str, Any], mod: dict[str, Any], server_state: str, ue4ss_text: str) -> dict[str, Any]:
    kind = str(mod.get("installKind") or "unknown")
    paths = _deployment_paths(instance, mod)
    existing = [str(path) for path in paths if path.exists()]
    checked_at = _now()
    if not existing:
        return {"state": "failed", "evidence": "Expected installed files are missing.", "confidence": "high", "checkedAt": checked_at, "paths": []}
    if kind == "ue4ss":
        explicit, loader_error, evidence = _ue4ss_mod_evidence(ue4ss_text, mod)
        state = "failed" if loader_error else "verified" if explicit else "warning"
        confidence = "medium" if loader_error else "high" if explicit else "medium"
        return {"state": state, "evidence": evidence, "confidence": confidence, "checkedAt": checked_at, "paths": existing}
    if kind == "palmod_nexus" or mod.get("workshopId"):
        manifests = [path for path in paths if path.name == "InstallManifest.json" and path.exists()]
        if manifests:
            return {"state": "verified", "evidence": "Palworld created InstallManifest.json for the deployed package.", "confidence": "high", "checkedAt": checked_at, "paths": existing}
        return {"state": "warning", "evidence": "Package files are present, but Palworld has not produced an InstallManifest.json yet.", "confidence": "medium", "checkedAt": checked_at, "paths": existing}
    if kind in {"pak", "logicmods", "workshop_pak"}:
        return {"state": "warning", "evidence": "PAK files are present and the server remained online. Palworld does not provide a universal per-mod load confirmation for this mod type.", "confidence": "low", "checkedAt": checked_at, "paths": existing}
    return {"state": "warning", "evidence": "Installed files are present, but no loader-specific verification method is available.", "confidence": "low", "checkedAt": checked_at, "paths": existing}


async def verify_after_start(ctx: Any, instance: dict[str, Any]) -> dict[str, Any]:
    ctx.progress(5, "Waiting for Palworld and mod loaders")
    ctx.log("Waiting 20 seconds for the dedicated server and mod loaders to initialize.")
    await asyncio.sleep(20)
    status = process_manager.get_status(instance["id"])
    server_state = str(status.get("state") or "unknown")
    if server_state not in {"online", "starting"}:
        message = "Mod startup verification failed because the Palworld process did not remain online."
        activity_log.log("error", instance["name"], message, instance_id=instance["id"])
        raise RuntimeError(message)
    mods = mods_store.load_mods(instance["id"])
    enabled_mods = [mod for mod in mods if mod.get("status") != "disabled"]
    ue4ss_log = _ue4ss_log(instance)
    ue4ss_text = ""
    if ue4ss_log.is_file():
        try:
            ue4ss_text = ue4ss_log.read_text(encoding="utf-8", errors="ignore")[-500000:]
        except OSError:
            pass
    verified = warnings = failed = 0
    results = []
    for index, mod in enumerate(enabled_mods):
        verification = _verification_for_mod(instance, mod, server_state, ue4ss_text)
        mod["runtimeVerification"] = verification
        state = verification["state"]
        if state == "verified":
            verified += 1; level = "info"
        elif state == "warning":
            warnings += 1; level = "warning"
        else:
            failed += 1; level = "error"
        results.append({"id": mod.get("id"), "name": mod.get("name"), "kind": mod.get("installKind") or "unknown", **verification})
        ctx.log(f"{mod.get('name')}: {state} - {verification['evidence']}", level)
        activity_log.log(level, instance["name"], f"Mod runtime verification: {mod.get('name')} — {state}. {verification['evidence']} Confidence: {verification['confidence']}.", instance_id=instance["id"])
        if mod.get("source") == "nexus":
            nexus_inventory.upsert(instance["id"], mod)
        ctx.progress(20 + ((index + 1) / max(1, len(enabled_mods))) * 70, f"Verified {index + 1}/{len(enabled_mods)} mods")
    mods_store.save_mods(instance["id"], mods)
    summary = f"Mod runtime verification completed: {verified} verified, {warnings} warning(s), {failed} failed."
    activity_log.log("info" if warnings == 0 and failed == 0 else "warning", instance["name"], summary, instance_id=instance["id"])
    ctx.progress(100, "Mod runtime verification complete")
    return {"serverState": server_state, "checked": len(enabled_mods), "verified": verified, "warnings": warnings, "failed": failed, "results": results, "ue4ssLog": str(ue4ss_log) if ue4ss_log.is_file() else None}

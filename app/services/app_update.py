"""GitHub release discovery and reliable Windows updater hand-off."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import httpx

from app.paths import cache_dir, data_dir, is_frozen
from app.services import app_event_log, notification_center
from app.version import (
    APP_CHANNEL,
    APP_VERSION,
    GITHUB_API_VERSION,
    GITHUB_REPOSITORY,
    UPDATE_CHECK_SECONDS,
)

logger = logging.getLogger("egm.update_service")
_FAILURE_CACHE_SECONDS = 60
_cache: dict[str, Any] | None = None
_cache_expires_at = 0.0
_lock = asyncio.Lock()
_install_task: asyncio.Task[None] | None = None
_VERSION_RE = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$",
    re.I,
)
_INSTALLER_RE = re.compile(r"(?:ExilesGameManager|Exiles-Game-Manager).*Setup.*\.exe$", re.I)
_SHA_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
_INSTALL_STATE: dict[str, Any] = {
    "installing": False,
    "installPhase": "idle",
    "installProgress": 0,
    "installMessage": None,
    "installError": None,
    "targetVersion": None,
}


def _set_install_state(
    phase: str,
    progress: int,
    message: str,
    *,
    error: str | None = None,
    target_version: str | None = None,
) -> None:
    _INSTALL_STATE.update(
        {
            "installing": phase not in {"idle", "failed"},
            "installPhase": phase,
            "installProgress": max(0, min(100, int(progress))),
            "installMessage": message,
            "installError": error,
        }
    )
    if target_version is not None:
        _INSTALL_STATE["targetVersion"] = target_version


def _version_tuple(value: str):
    match = _VERSION_RE.fullmatch(value.strip())
    if not match:
        return None
    prerelease = match.group("pre")
    pre_parts = []
    if prerelease:
        for part in prerelease.split("."):
            pre_parts.append((0, int(part)) if part.isdigit() else (1, part.lower()))
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        0 if prerelease else 1,
        tuple(pre_parts),
    )


def _base_status(message: str | None = None) -> dict[str, Any]:
    status = {
        "currentVersion": APP_VERSION,
        "latestVersion": None,
        "updateAvailable": False,
        "releaseUrl": None,
        "releaseName": None,
        "publishedAt": None,
        "available": False,
        "configured": bool(GITHUB_REPOSITORY and "/" in GITHUB_REPOSITORY),
        "message": message,
        "installerAvailable": False,
        "installSupported": bool(os.name == "nt" and is_frozen()),
        "channel": APP_CHANNEL,
        "repository": GITHUB_REPOSITORY,
    }
    status.update(_INSTALL_STATE)
    return status


def _select_release(releases: list[dict[str, Any]]) -> dict[str, Any] | None:
    for release in releases:
        if release.get("draft"):
            continue
        if APP_CHANNEL == "stable" and release.get("prerelease"):
            continue
        if _version_tuple(str(release.get("tag_name") or "")):
            return release
    return None


def _asset(release: dict[str, Any], pattern: re.Pattern[str]) -> dict[str, Any] | None:
    return next(
        (
            asset
            for asset in release.get("assets", [])
            if pattern.search(str(asset.get("name") or ""))
        ),
        None,
    )


def _publish_update_notification(status: dict[str, Any]) -> None:
    if not status.get("updateAvailable"):
        return
    marker = data_dir() / "update_notification.json"
    latest = str(status.get("latestVersion") or "")
    try:
        previous = marker.read_text(encoding="utf-8-sig").strip() if marker.is_file() else ""
    except OSError:
        previous = ""
    if previous == latest:
        return
    notification_center.publish(
        "info",
        "notifications.appUpdate.title",
        "notifications.appUpdate.message",
        params={"version": latest},
        category="application_update",
        audience="super_admin",
        fallback_title="New EGM version available",
        fallback_message=f"Exiles Game Manager {latest} is ready to install.",
        action_url="/super-admin",
    )
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(latest, encoding="utf-8")


async def get_status(*, force: bool = False) -> dict[str, Any]:
    global _cache, _cache_expires_at
    if not GITHUB_REPOSITORY or "/" not in GITHUB_REPOSITORY:
        return _base_status("Update service not configured.")

    now = time.monotonic()
    if not force and _cache is not None and now < _cache_expires_at:
        result = dict(_cache)
        result.update(_INSTALL_STATE)
        return result

    async with _lock:
        now = time.monotonic()
        if not force and _cache is not None and now < _cache_expires_at:
            result = dict(_cache)
            result.update(_INSTALL_STATE)
            return result

        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": f"ExilesGameManager/{APP_VERSION}",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
            }
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(
                    f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases?per_page=20",
                    headers=headers,
                )
                response.raise_for_status()

            release = _select_release(response.json())
            if not release:
                raise ValueError("No supported release exists.")

            tag = str(release.get("tag_name") or "").strip()
            latest = _version_tuple(tag)
            current = _version_tuple(APP_VERSION)
            if latest is None or current is None:
                raise ValueError("Unsupported version metadata.")

            installer = _asset(release, _INSTALLER_RE)
            checksum = next(
                (
                    asset
                    for asset in release.get("assets", [])
                    if installer
                    and str(asset.get("name") or "").lower()
                    in {
                        f"{installer.get('name')}.sha256.txt".lower(),
                        f"{installer.get('name')}.sha256".lower(),
                    }
                ),
                None,
            )
            if checksum is None:
                checksum = _asset(
                    release,
                    re.compile(r"sha256.*\.txt$|\.sha256(?:\.txt)?$", re.I),
                )

            _cache = {
                "currentVersion": APP_VERSION,
                "latestVersion": tag.lstrip("vV"),
                "updateAvailable": latest > current,
                "releaseUrl": str(release.get("html_url") or ""),
                "releaseName": str(release.get("name") or tag),
                "publishedAt": release.get("published_at"),
                "available": True,
                "configured": True,
                "message": None,
                "installerAvailable": installer is not None and checksum is not None,
                "installSupported": bool(os.name == "nt" and is_frozen()),
                "installerUrl": installer.get("browser_download_url") if installer else None,
                "installerName": installer.get("name") if installer else None,
                "checksumUrl": checksum.get("browser_download_url") if checksum else None,
                "channel": APP_CHANNEL,
                "repository": GITHUB_REPOSITORY,
            }
            _cache_expires_at = time.monotonic() + UPDATE_CHECK_SECONDS
            _publish_update_notification(_cache)
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Update server is currently unavailable: %s", exc)
            _cache = _base_status("Update server is currently unavailable.")
            _cache["configured"] = True
            _cache_expires_at = time.monotonic() + _FAILURE_CACHE_SECONDS

        result = dict(_cache)
        result.update(_INSTALL_STATE)
        return result


async def _download(
    client: httpx.AsyncClient,
    url: str,
    destination: Path,
    progress: Callable[[int], None],
) -> None:
    async with client.stream("GET", url) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length") or 0)
        received = 0
        with destination.open("wb") as handle:
            async for chunk in response.aiter_bytes(1024 * 256):
                handle.write(chunk)
                received += len(chunk)
                if total > 0:
                    progress(min(90, int(received * 90 / total)))


def _completion_marker_path() -> Path:
    return cache_dir() / "update-completed.json"


def _powershell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _restart_executable_path() -> Path:
    return Path(sys.executable if is_frozen() else sys.argv[0]).resolve()


def _create_handoff_script(installer: Path, version: str) -> Path:
    update_dir = installer.parent
    script_path = update_dir / "EGM-Update-Handoff.ps1"
    marker = _completion_marker_path()
    executable = _restart_executable_path()
    parent_pid = os.getpid()

    script = f"""$ErrorActionPreference = 'Stop'
$parentPid = {parent_pid}
$installer = {_powershell_single_quote(str(installer))}
$restartExe = {_powershell_single_quote(str(executable))}
$marker = {_powershell_single_quote(str(marker))}
$version = {_powershell_single_quote(version)}

while (Get-Process -Id $parentPid -ErrorAction SilentlyContinue) {{
    Start-Sleep -Milliseconds 250
}}
Start-Sleep -Milliseconds 750

$arguments = @(
    '/UPDATE',
    '/VERYSILENT',
    '/SUPPRESSMSGBOXES',
    '/NORESTART',
    '/CLOSEAPPLICATIONS',
    '/FORCECLOSEAPPLICATIONS',
    '/SP-'
)

$exitCode = -1
$errorMessage = $null
try {{
    $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
    $exitCode = $process.ExitCode
}} catch {{
    $errorMessage = $_.Exception.Message
}}

$success = ($exitCode -eq 0)
$result = @{{
    version = $version
    success = $success
    exitCode = $exitCode
    error = $errorMessage
    completedAt = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
}} | ConvertTo-Json -Compress

New-Item -ItemType Directory -Path (Split-Path -Parent $marker) -Force | Out-Null
[System.IO.File]::WriteAllText($marker, $result, (New-Object System.Text.UTF8Encoding($false)))

if ($success -and (Test-Path -LiteralPath $restartExe -PathType Leaf)) {{
    Start-Process -FilePath $restartExe -WorkingDirectory (Split-Path -Parent $restartExe)
}}
"""
    script_path.write_text(script, encoding="utf-8-sig")
    return script_path


def _launch_handoff(script_path: Path) -> None:
    creation_flags = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(script_path),
        ],
        cwd=str(script_path.parent),
        creationflags=creation_flags,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def _run_install() -> None:
    try:
        _set_install_state("checking", 3, "Checking the GitHub release…")
        status = await get_status(force=True)
        version = str(status.get("latestVersion") or "")
        _set_install_state(
            "downloading",
            5,
            "Downloading the verified EGM installer…",
            target_version=version,
        )

        if not status.get("updateAvailable"):
            raise RuntimeError("No newer EGM version is available.")
        if not status.get("installerUrl"):
            raise RuntimeError("The GitHub release does not contain an EGM Setup executable.")
        if not status.get("checksumUrl"):
            raise RuntimeError("The GitHub release does not contain the required SHA-256 checksum.")

        update_dir = cache_dir() / "updates" / version
        update_dir.mkdir(parents=True, exist_ok=True)
        installer = update_dir / str(status.get("installerName") or "ExilesGameManager-Setup.exe")
        installer.unlink(missing_ok=True)

        async with httpx.AsyncClient(
            timeout=300,
            follow_redirects=True,
            headers={"User-Agent": f"ExilesGameManager/{APP_VERSION}"},
        ) as client:
            await _download(
                client,
                str(status["installerUrl"]),
                installer,
                lambda percent: _set_install_state(
                    "downloading",
                    5 + int(percent * 0.7),
                    "Downloading the verified EGM installer…",
                    target_version=version,
                ),
            )

            _set_install_state(
                "verifying",
                78,
                "Verifying the published SHA-256 checksum…",
                target_version=version,
            )
            checksum_response = await client.get(str(status["checksumUrl"]))
            checksum_response.raise_for_status()
            match = _SHA_RE.search(checksum_response.text)
            if not match:
                raise RuntimeError("The release checksum file is invalid.")

            expected = match.group(0).lower()
            actual = hashlib.sha256(installer.read_bytes()).hexdigest().lower()
            if actual != expected:
                installer.unlink(missing_ok=True)
                raise RuntimeError("The downloaded installer failed SHA-256 verification.")

        _set_install_state(
            "preparing",
            90,
            "Preparing the automatic update hand-off…",
            target_version=version,
        )
        script_path = _create_handoff_script(installer, version)
        _launch_handoff(script_path)

        app_event_log.log(
            "info",
            "EGM Update",
            f"Verified update {version} downloaded. Automatic installation is starting.",
            version=version,
            installer=installer.name,
        )
        _set_install_state(
            "closing",
            100,
            "Closing EGM. The update will install and EGM will restart automatically…",
            target_version=version,
        )
        await asyncio.sleep(2.0)
        os._exit(0)
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        logger.exception("Automatic EGM update failed: %s", message)
        app_event_log.log("error", "EGM Update", f"Automatic update failed: {message}")
        _set_install_state("failed", 0, "The automatic update failed.", error=message)


async def install_update() -> dict[str, Any]:
    global _install_task
    if os.name != "nt" or not is_frozen():
        raise RuntimeError("Automatic installation is available only in the installed Windows edition.")
    if _install_task is not None and not _install_task.done():
        return {
            "ok": True,
            "accepted": True,
            "message": "The update is already being prepared.",
        }

    _set_install_state("queued", 1, "Preparing the automatic update…")
    _install_task = asyncio.create_task(_run_install(), name="egm-automatic-update")
    return {
        "ok": True,
        "accepted": True,
        "message": "The automatic update has started.",
    }


def consume_completion_marker() -> dict[str, Any] | None:
    marker = _completion_marker_path()
    if not marker.is_file():
        return None
    try:
        result = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError):
        marker.unlink(missing_ok=True)
        return None
    marker.unlink(missing_ok=True)

    version = str(result.get("version") or APP_VERSION)
    if result.get("success"):
        app_event_log.log(
            "info",
            "EGM Update",
            f"Update completed successfully. EGM is now running version {APP_VERSION}.",
            installedVersion=APP_VERSION,
            requestedVersion=version,
            installerExitCode=result.get("exitCode"),
        )
        notification_center.publish(
            "success",
            "notifications.appUpdate.completedTitle",
            "notifications.appUpdate.completedMessage",
            params={"version": APP_VERSION},
            category="application_update",
            audience="super_admin",
            fallback_title="EGM update completed",
            fallback_message=f"Exiles Game Manager was updated successfully to {APP_VERSION}.",
            action_url="/activity",
        )
    else:
        error = str(result.get("error") or f"Installer exit code {result.get('exitCode')}")
        app_event_log.log(
            "error",
            "EGM Update",
            f"Update installation failed: {error}",
            requestedVersion=version,
            installerExitCode=result.get("exitCode"),
        )
    return result

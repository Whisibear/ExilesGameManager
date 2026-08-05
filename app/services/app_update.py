"""GitHub release discovery and reliable Windows updater hand-off."""
from __future__ import annotations

import asyncio
import base64
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
from app.services import app_event_log, notification_center, update_history
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



def _log_update_step(level: str, message: str, **details: Any) -> None:
    update_history.append_runtime_log(level, message, **details)
    logger_method = getattr(logger, level.lower(), logger.info)
    logger_method("%s | %s", message, details if details else "")
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


def _restart_executable_path() -> Path:
    return Path(sys.executable if is_frozen() else sys.argv[0]).resolve()


def _update_worker_path() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent / "EGMUpdateWorker.exe"
    return Path(__file__).resolve().parents[2] / "dist" / "EGMUpdateWorker.exe"


def _handoff_log_path(installer: Path) -> Path:
    return installer.parent / "update_worker.log"


def _installer_log_path(installer: Path) -> Path:
    return installer.parent / "installer_update.log"


def _validated_update_path(path: Path, *, must_exist: bool = False) -> Path:
    raw = str(path).strip()
    if raw in {"", "\\", "\\\\", "/", "."}:
        raise RuntimeError(f"Unsafe update path was rejected: {raw!r}")

    resolved = path.expanduser().resolve(strict=False)
    text = str(resolved).strip()
    if not resolved.is_absolute():
        raise RuntimeError(f"Update path is not absolute: {path}")
    if text in {"", "\\", "\\\\", "/", "."}:
        raise RuntimeError(f"Unsafe update path was rejected: {text!r}")
    if must_exist and not resolved.is_file():
        raise RuntimeError(f"Required update file is missing: {resolved}")
    return resolved


def _encode_job_value(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _write_update_worker_job(
    installer: Path,
    version: str,
    sha256: str,
) -> Path:
    worker = _validated_update_path(_update_worker_path(), must_exist=True)
    installer = _validated_update_path(installer, must_exist=True)
    restart_executable = _validated_update_path(
        _restart_executable_path(),
        must_exist=False,
    )
    marker = _validated_update_path(_completion_marker_path())
    handoff_log = _validated_update_path(_handoff_log_path(installer))
    installer_log = _validated_update_path(_installer_log_path(installer))
    job_path = _validated_update_path(installer.parent / "update_worker.job")

    values = {
        "worker": str(worker),
        "parent-pid": str(os.getpid()),
        "installer": str(installer),
        "restart": str(restart_executable),
        "marker": str(marker),
        "handoff-log": str(handoff_log),
        "installer-log": str(installer_log),
        "from": APP_VERSION,
        "to": version,
        "sha256": sha256,
    }
    payload = "\n".join(
        f"{key}={_encode_job_value(value)}"
        for key, value in values.items()
    )
    job_path.write_text(payload + "\n", encoding="ascii")
    return job_path


def _launch_update_worker(
    installer: Path,
    version: str,
    sha256: str,
) -> subprocess.Popen[bytes]:
    worker_path = _update_worker_path()
    if not worker_path.is_file():
        raise RuntimeError(
            f"The native EGM UpdateWorker is missing: {worker_path}"
        )

    worker = _validated_update_path(worker_path, must_exist=True)
    job_path = _write_update_worker_job(installer, version, sha256)
    bootstrap_log = _validated_update_path(
        installer.parent / "update_worker_bootstrap.log"
    )
    log_handle = bootstrap_log.open("ab", buffering=0)
    creation_flags = (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
    )
    environment = os.environ.copy()
    environment["EGM_UPDATE_JOB"] = str(job_path)

    _log_update_step(
        "info",
        "Native UpdateWorker job created",
        worker=str(worker),
        job=str(job_path),
        installer=str(_validated_update_path(installer, must_exist=True)),
        restart=str(
            _validated_update_path(
                _restart_executable_path(),
                must_exist=False,
            )
        ),
    )

    try:
        return subprocess.Popen(
            [str(worker)],
            cwd=str(installer.parent.resolve()),
            env=environment,
            creationflags=creation_flags,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
    finally:
        log_handle.close()


async def _run_install() -> None:
    try:
        started_monotonic = time.monotonic()
        started_at = time.time()
        previous_version = APP_VERSION
        _log_update_step("info", "Update requested", currentVersion=previous_version, channel=APP_CHANNEL, source="github")
        _set_install_state("checking", 3, "Checking the GitHub release…")
        _log_update_step("info", "Checking GitHub release", repository=GITHUB_REPOSITORY)
        status = await get_status(force=True)
        version = str(status.get("latestVersion") or "")
        _log_update_step("info", "New release selected", currentVersion=previous_version, targetVersion=version, releaseUrl=status.get("releaseUrl"))
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

        _log_update_step("info", "Downloading installer", installer=status.get("installerName"), targetVersion=version)
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
            _log_update_step("info", "Installer download completed", installer=installer.name, sizeBytes=installer.stat().st_size)
            _log_update_step("info", "Downloading checksum", checksumUrl=status.get("checksumUrl"))
            checksum_response = await client.get(str(status["checksumUrl"]))
            checksum_response.raise_for_status()
            match = _SHA_RE.search(checksum_response.text)
            if not match:
                raise RuntimeError("The release checksum file is invalid.")

            expected = match.group(0).lower()
            actual = hashlib.sha256(installer.read_bytes()).hexdigest().lower()
            if actual != expected:
                _log_update_step("error", "SHA-256 verification failed", expected=expected, actual=actual, installer=installer.name)
                installer.unlink(missing_ok=True)
                raise RuntimeError("The downloaded installer failed SHA-256 verification.")

        _log_update_step("info", "SHA-256 verification successful", sha256=actual, installer=installer.name)
        _set_install_state(
            "preparing",
            90,
            "Preparing the automatic update hand-off…",
            target_version=version,
        )
        handoff_process = _launch_update_worker(installer, version, actual)
        _log_update_step(
            "info",
            "Native UpdateWorker launched",
            targetVersion=version,
            launcherPid=handoff_process.pid,
            worker=str(_update_worker_path()),
            handoffLog=str(_handoff_log_path(installer)),
            bootstrapLog=str(installer.parent / "update_worker_bootstrap.log"),
            job=str(installer.parent / "update_worker.job"),
            installerLog=str(_installer_log_path(installer)),
        )

        await asyncio.sleep(1.5)
        handoff_exit_code = handoff_process.poll()
        if handoff_exit_code is not None:
            bootstrap_log = installer.parent / "update_worker_bootstrap.log"
            bootstrap_details = ""
            try:
                bootstrap_details = bootstrap_log.read_text(
                    encoding="utf-8-sig",
                    errors="replace",
                )[-4000:]
            except OSError:
                pass
            raise RuntimeError(
                "The native UpdateWorker terminated before Setup started "
                f"(exit code {handoff_exit_code}). "
                f"Bootstrap log: {bootstrap_log}. {bootstrap_details}"
            )

        _log_update_step(
            "info",
            "Native UpdateWorker startup verified",
            launcherPid=handoff_process.pid,
            targetVersion=version,
        )

        app_event_log.log(
            "info",
            "EGM Update",
            f"Verified update {version} downloaded. Automatic installation is starting.",
            version=version,
            installer=installer.name,
        )
        update_history.append_history({
            "from": previous_version,
            "to": version,
            "channel": APP_CHANNEL,
            "source": "github",
            "installer": installer.name,
            "sha256": actual,
            "sha256Verified": True,
            "status": "handoff_started",
            "startedAt": started_at,
            "handoffAt": time.time(),
        })
        _set_install_state(
            "closing",
            100,
            "Closing EGM. The update will install and EGM will restart automatically…",
            target_version=version,
        )
        await asyncio.sleep(2.0)
        _log_update_step(
            "info",
            "EGM process exiting for installer takeover",
            targetVersion=version,
        )
        os._exit(0)
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        _log_update_step("error", "Automatic update failed", error=message)
        update_history.append_history({
            "from": APP_VERSION,
            "to": _INSTALL_STATE.get("targetVersion"),
            "channel": APP_CHANNEL,
            "source": "github",
            "status": "failed",
            "error": message,
            "completedAt": time.time(),
        })
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
        previous_version = str(result.get("fromVersion") or "unknown")
        started_at = result.get("startedAt")
        completed_at = result.get("completedAt")
        duration_seconds = None
        if isinstance(started_at, (int, float)) and isinstance(completed_at, (int, float)):
            duration_seconds = round(float(completed_at) - float(started_at), 2)

        detailed_message = (
            f"New EGM version installed successfully: {previous_version} → {APP_VERSION}. "
            f"Source: GitHub Release. SHA-256: verified. Installer exit code: {result.get('exitCode')}. "
            f"Automatic restart: completed."
        )
        app_event_log.log(
            "info",
            "New EGM Version Installed",
            detailed_message,
            previousVersion=previous_version,
            installedVersion=APP_VERSION,
            requestedVersion=version,
            channel=APP_CHANNEL,
            source="github",
            sha256Verified=True,
            installer=result.get("installer"),
            installerExitCode=result.get("exitCode"),
            automaticRestart=True,
            durationSeconds=duration_seconds,
            startedAt=started_at,
            completedAt=completed_at,
        )
        _log_update_step(
            "info",
            "Update completed successfully",
            previousVersion=previous_version,
            installedVersion=APP_VERSION,
            installerExitCode=result.get("exitCode"),
            durationSeconds=duration_seconds,
        )
        update_history.append_history({
            "from": previous_version,
            "to": APP_VERSION,
            "requestedVersion": version,
            "channel": APP_CHANNEL,
            "source": "github",
            "installer": result.get("installer"),
            "sha256": result.get("sha256"),
            "sha256Verified": True,
            "installerExitCode": result.get("exitCode"),
            "automaticRestart": True,
            "durationSeconds": duration_seconds,
            "status": "success",
            "startedAt": started_at,
            "completedAt": completed_at,
        })
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
            "EGM Update Failed",
            f"Automatic update installation failed for {version}: {error}",
            previousVersion=result.get("fromVersion"),
            requestedVersion=version,
            installer=result.get("installer"),
            installerExitCode=result.get("exitCode"),
            automaticRestart=False,
        )
        _log_update_step(
            "error",
            "Installer failed",
            requestedVersion=version,
            installerExitCode=result.get("exitCode"),
            error=error,
        )
        update_history.append_history({
            "from": result.get("fromVersion"),
            "to": version,
            "channel": APP_CHANNEL,
            "source": "github",
            "installer": result.get("installer"),
            "sha256": result.get("sha256"),
            "sha256Verified": result.get("sha256Verified"),
            "installerExitCode": result.get("exitCode"),
            "automaticRestart": False,
            "status": "failed",
            "error": error,
            "startedAt": result.get("startedAt"),
            "completedAt": result.get("completedAt"),
        })
    return result

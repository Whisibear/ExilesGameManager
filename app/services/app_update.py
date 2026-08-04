
"""GitHub release discovery and safe Windows installer hand-off."""
from __future__ import annotations
import asyncio, hashlib, json, logging, os, re, subprocess, sys, threading, time
from pathlib import Path
from typing import Any
import httpx
from app.paths import data_dir, is_frozen
from app.services import notification_center
from app.version import APP_CHANNEL, APP_VERSION, GITHUB_API_VERSION, GITHUB_REPOSITORY, UPDATE_CHECK_SECONDS
logger = logging.getLogger("egm.update_service")
_FAILURE_CACHE_SECONDS = 60
_cache: dict[str, Any] | None = None
_cache_expires_at = 0.0
_lock = asyncio.Lock()
_VERSION_RE = re.compile(r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$", re.I)
_INSTALLER_RE = re.compile(r"(?:ExilesGameManager|Exiles-Game-Manager).*Setup.*\.exe$", re.I)
_SHA_RE = re.compile(r"^[0-9a-fA-F]{64}")

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

def _base_status(message=None):
    return {
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
        "installing": False,
        "channel": APP_CHANNEL,
        "repository": GITHUB_REPOSITORY,
    }

def _select_release(releases):
    for release in releases:
        if release.get("draft"): continue
        if APP_CHANNEL=="stable" and release.get("prerelease"): continue
        if _version_tuple(str(release.get("tag_name") or "")): return release
    return None

def _asset(release, pattern):
    return next((a for a in release.get("assets",[]) if pattern.search(str(a.get("name") or ""))),None)

def _publish_update_notification(status):
    if not status.get("updateAvailable"): return
    marker=data_dir()/"update_notification.json"; latest=str(status.get("latestVersion") or "")
    try: previous=marker.read_text(encoding="utf-8-sig").strip() if marker.is_file() else ""
    except OSError: previous=""
    if previous==latest: return
    notification_center.publish("info","notifications.appUpdate.title","notifications.appUpdate.message",params={"version":latest},category="application_update",audience="super_admin",fallback_title="New EGM version available",fallback_message=f"Exiles Game Manager {latest} is ready to install.",action_url="/super-admin")
    marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text(latest,encoding="utf-8")

async def get_status(*,force=False):
    global _cache,_cache_expires_at
    if not GITHUB_REPOSITORY or "/" not in GITHUB_REPOSITORY: return _base_status("Update service not configured.")
    now=time.monotonic()
    if not force and _cache is not None and now<_cache_expires_at: return dict(_cache)
    async with _lock:
        now=time.monotonic()
        if not force and _cache is not None and now<_cache_expires_at: return dict(_cache)
        try:
            headers={"Accept":"application/vnd.github+json","User-Agent":f"ExilesGameManager/{APP_VERSION}","X-GitHub-Api-Version":GITHUB_API_VERSION}
            async with httpx.AsyncClient(timeout=10,follow_redirects=True) as client:
                response=await client.get(f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases?per_page=20",headers=headers); response.raise_for_status()
            release=_select_release(response.json())
            if not release: raise ValueError("No supported release exists.")
            tag=str(release.get("tag_name") or "").strip(); latest=_version_tuple(tag); current=_version_tuple(APP_VERSION)
            if latest is None or current is None: raise ValueError("Unsupported version metadata.")
            installer=_asset(release,_INSTALLER_RE); checksum = next((a for a in release.get("assets", []) if installer and str(a.get("name") or "").lower() in {f"{installer.get('name')}.sha256.txt".lower(), f"{installer.get('name')}.sha256".lower()}), None)
            if checksum is None:
                checksum=_asset(release,re.compile(r"sha256.*\.txt$|\.sha256(?:\.txt)?$",re.I))
            _cache={"currentVersion":APP_VERSION,"latestVersion":tag.lstrip("vV"),"updateAvailable":latest>current,"releaseUrl":str(release.get("html_url") or ""),"releaseName":str(release.get("name") or tag),"publishedAt":release.get("published_at"),"available":True,"configured":True,"message":None,"installerAvailable":installer is not None,"installSupported":bool(os.name=="nt" and is_frozen()),"installing":False,"installerUrl":installer.get("browser_download_url") if installer else None,"installerName":installer.get("name") if installer else None,"checksumUrl": checksum.get("browser_download_url") if checksum else None, "channel": APP_CHANNEL, "repository": GITHUB_REPOSITORY}
            _cache_expires_at=time.monotonic()+UPDATE_CHECK_SECONDS; _publish_update_notification(_cache)
        except (httpx.HTTPError,ValueError,TypeError) as exc:
            logger.warning("Update server is currently unavailable: %s",exc); _cache=_base_status("Update server is currently unavailable."); _cache["configured"]=True; _cache_expires_at=time.monotonic()+_FAILURE_CACHE_SECONDS
        return dict(_cache)

async def _download(client,url,destination):
    async with client.stream("GET",url) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            async for chunk in response.aiter_bytes(1024*1024): handle.write(chunk)

async def prepare_installer():
    if os.name!="nt" or not is_frozen(): raise RuntimeError("Automatic installation is available only in the installed Windows edition.")
    status=await get_status(force=True)
    if not status.get("updateAvailable"): raise RuntimeError("No newer EGM version is available.")
    url=str(status.get("installerUrl") or "")
    if not url: raise RuntimeError("The GitHub release does not contain an EGM Setup executable.")
    update_dir=data_dir()/"updates"/str(status["latestVersion"]); update_dir.mkdir(parents=True,exist_ok=True)
    installer=update_dir/str(status.get("installerName") or "ExilesGameManager-Setup.exe")
    async with httpx.AsyncClient(timeout=180,follow_redirects=True,headers={"User-Agent":f"ExilesGameManager/{APP_VERSION}"}) as client:
        await _download(client,url,installer)
        checksum_url=str(status.get("checksumUrl") or "")
        if checksum_url:
            response=await client.get(checksum_url); response.raise_for_status(); match=_SHA_RE.search(response.text.strip())
            if not match: installer.unlink(missing_ok=True); raise RuntimeError("The release checksum file is invalid.")
            if hashlib.sha256(installer.read_bytes()).hexdigest()!=match.group(0).lower(): installer.unlink(missing_ok=True); raise RuntimeError("The downloaded installer failed SHA256 verification.")
    return {"installer":str(installer),"version":status["latestVersion"]}

def _restart_executable_path() -> Path:
    return Path(sys.executable if is_frozen() else sys.argv[0]).resolve()


def _restart_marker_path() -> Path:
    return data_dir() / "updates" / "restart.json"


def _installer_command(installer: Path) -> list[str]:
    restart_path = _restart_executable_path()
    return [
        str(installer),
        "/UPDATE",
        "/VERYSILENT",
        "/SUPPRESSMSGBOXES",
        "/NORESTART",
        "/CLOSEAPPLICATIONS",
        "/FORCECLOSEAPPLICATIONS",
        "/SP-",
        f"/EGMRESTART={restart_path}",
    ]


def _launch_and_exit(installer: Path) -> None:
    def worker() -> None:
        time.sleep(1.5)
        restart_marker = _restart_marker_path()
        restart_marker.parent.mkdir(parents=True, exist_ok=True)
        restart_marker.write_text(json.dumps({"installer": installer.name, "requestedAt": time.time()}), encoding="utf-8")
        command = _installer_command(installer)
        logger.info("Starting verified EGM update installer: %s", installer.name)
        subprocess.Popen(
            command,
            cwd=str(installer.parent),
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            close_fds=True,
        )
        time.sleep(1)
        os._exit(0)

    threading.Thread(target=worker, name="egm-updater", daemon=True).start()

async def install_update():
    prepared=await prepare_installer(); _launch_and_exit(Path(prepared["installer"]))
    return {"ok":True,"version":prepared["version"],"message":"The update installer is starting. EGM will close automatically."}

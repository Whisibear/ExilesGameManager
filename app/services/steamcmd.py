"""SteamCMD bootstrap, server installation, and external interactive console support."""

import asyncio
import logging
import os
import re
import subprocess
import zipfile
from collections.abc import Callable
from pathlib import Path

import httpx

from app.paths import data_dir
from app.services import activity_log
from app.services.windows_subprocess import hidden_process_kwargs

logger = logging.getLogger("egm.steamcmd")

STEAMCMD_DIR = data_dir() / "steamcmd"
STEAMCMD_DIR.mkdir(parents=True, exist_ok=True)
_STEAMCMD_LOCK = asyncio.Lock()
STEAMCMD_EXE = STEAMCMD_DIR / "steamcmd.exe"
STEAMCMD_ZIP_URL = "https://client-update.steamstatic.com/installer/steamcmd.zip"
PALSERVER_APP_ID = "2394010"
_PUBLIC_BUILD_RE = re.compile(r'"public"\s*\{.*?"buildid"\s*"(?P<buildid>\d+)"', re.DOTALL)


class SteamCmdError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _redact_args(args: list[str]) -> list[str]:
    redacted = [str(arg) for arg in args]
    for index, value in enumerate(redacted):
        if value == "+login" and index + 1 < len(redacted) and redacted[index + 1].lower() != "anonymous":
            redacted[index + 1] = "<steam-user>"
            if index + 2 < len(redacted):
                redacted[index + 2] = "********"
    return redacted


async def _run(args: list[str], on_output: Callable[[str], None] | None = None) -> int:
    async with _STEAMCMD_LOCK:
        logger.info("steamcmd: running %s", " ".join(_redact_args(args)))
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            **hidden_process_kwargs(),
        )
        assert process.stdout is not None
        async for raw_line in process.stdout:
            line = raw_line.decode(errors="replace").rstrip()
            if line:
                logger.info("steamcmd: %s", line)
                if on_output:
                    on_output(line)
        return await process.wait()


async def ensure_steamcmd() -> Path:
    if STEAMCMD_EXE.is_file():
        return STEAMCMD_EXE
    logger.info("steamcmd: bootstrapping from %s", STEAMCMD_ZIP_URL)
    zip_path = STEAMCMD_DIR / "steamcmd.zip"
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(STEAMCMD_ZIP_URL)
            response.raise_for_status()
            zip_path.write_bytes(response.content)
    except httpx.HTTPError as exc:
        raise SteamCmdError(f"Couldn't download SteamCMD: {exc}") from exc
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(STEAMCMD_DIR)
    except zipfile.BadZipFile as exc:
        raise SteamCmdError("The downloaded SteamCMD archive was corrupt. Try again.") from exc
    finally:
        zip_path.unlink(missing_ok=True)
    if not STEAMCMD_EXE.is_file():
        raise SteamCmdError("Downloaded SteamCMD, but steamcmd.exe wasn't found after extracting it.")
    await _run([str(STEAMCMD_EXE), "+quit"])
    return STEAMCMD_EXE


async def open_interactive_console() -> dict[str, object]:
    """Open the normal SteamCMD console without redirecting input or output.

    EGM never receives, stores, or logs commands, account names, passwords, or
    Steam Guard codes entered in this external console.
    """
    exe = await ensure_steamcmd()
    try:
        if os.name == "nt":
            subprocess.Popen(
                [str(exe)],
                cwd=str(STEAMCMD_DIR),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                close_fds=True,
            )
        else:
            raise SteamCmdError("The external SteamCMD console is currently supported on Windows only.")
    except OSError as exc:
        raise SteamCmdError(f"Could not open the SteamCMD console: {exc}") from exc
    activity_log.log("info", "SteamCMD", "External SteamCMD console opened by the Super Admin.")
    return {
        "opened": True,
        "workingDirectory": str(STEAMCMD_DIR),
        "workshopContentDirectory": str(STEAMCMD_DIR / "steamapps" / "workshop" / "content" / "1623730"),
    }


async def disconnect_authenticated_session() -> None:
    """Compatibility no-op retained for application shutdown."""
    return None


def authenticated_session_library_roots() -> list[Path]:
    return []

def authenticated_session_status() -> dict[str, object]:
    return {"connected": False, "state": "disconnected", "expiresInSeconds": 0}


async def install_palserver(install_dir: Path, on_output: Callable[[str], None] | None = None) -> None:
    exe = await ensure_steamcmd()
    install_dir.mkdir(parents=True, exist_ok=True)
    args = [str(exe), "+force_install_dir", str(install_dir), "+login", "anonymous", "+app_update", PALSERVER_APP_ID, "validate", "+quit"]
    returncode = await _run(args, on_output)
    if returncode != 0:
        logger.warning("steamcmd: exited %s, retrying once", returncode)
        if on_output:
            on_output("SteamCMD self-updated - retrying the install...")
        returncode = await _run(args, on_output)
        if returncode != 0:
            raise SteamCmdError(f"SteamCMD exited with code {returncode}. Check the deploy log for details.")
    if not (install_dir / "PalServer.exe").is_file():
        raise SteamCmdError("SteamCMD finished, but PalServer.exe wasn't found in the install folder.")


def installed_build_id(install_dir: Path) -> str | None:
    manifest = install_dir / "steamapps" / f"appmanifest_{PALSERVER_APP_ID}.acf"
    if not manifest.is_file():
        return None
    try:
        text = manifest.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = re.search(r'"buildid"\s*"(?P<buildid>\d+)"', text)
    return match.group("buildid") if match else None


async def latest_public_build_id(on_output: Callable[[str], None] | None = None) -> str | None:
    exe = await ensure_steamcmd()
    lines: list[str] = []
    def collect(line: str) -> None:
        lines.append(line)
        if on_output:
            on_output(line)
    args = [str(exe), "+login", "anonymous", "+app_info_update", "1", "+app_info_print", PALSERVER_APP_ID, "+quit"]
    returncode = await _run(args, collect)
    if returncode != 0:
        raise SteamCmdError(f"SteamCMD exited with code {returncode} while checking for updates.")
    output = "\n".join(lines)
    match = _PUBLIC_BUILD_RE.search(output)
    if match:
        return match.group("buildid")
    fallback = re.search(r'"buildid"\s*"(?P<buildid>\d+)"', output)
    return fallback.group("buildid") if fallback else None

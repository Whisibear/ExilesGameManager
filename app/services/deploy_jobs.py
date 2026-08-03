"""Runs a fresh server deployment (SteamCMD install + initial settings +
instance registration) as a background task, since the SteamCMD download can
take several minutes. The frontend polls get_job() for live progress.
"""

import asyncio
import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.paths import default_servers_dir
from app.services import firewall, instance_store, palworld_settings, steamcmd
from app.services.steamcmd import SteamCmdError

logger = logging.getLogger("egm.deploy_jobs")

_jobs: dict[str, dict[str, Any]] = {}
_MAX_LOG_LINES = 300


def _sanitize_server_folder_name(name: str) -> str:
    """A server's own folder name, derived from what the user typed. Strips
    anything that isn't a safe filename character, then strips leading/
    trailing dots and spaces too - character-class filtering alone still
    lets a name of exactly "." or ".." straight through (both are made only
    of otherwise-allowed characters), which would resolve to the servers
    folder itself or its parent."""
    cleaned = re.sub(r"[^A-Za-z0-9 _.\-]", "", name).strip(". ")
    return cleaned or "Server"


def install_dir_for(name: str, parent_dir: Path | None = None) -> Path:
    """Every new deployment gets its own sanitized folder name. By default it
    lives under Documents\\ExilesGameManager\\Servers; super admins may choose a
    different existing parent folder for large installs or alternate drives."""
    base = parent_dir or default_servers_dir()
    return base / _sanitize_server_folder_name(name)


def default_install_dir(name: str) -> Path:
    return install_dir_for(name)


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def _append(job_id: str, line: str) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    job["log"].append(line)
    if len(job["log"]) > _MAX_LOG_LINES:
        job["log"] = job["log"][-_MAX_LOG_LINES:]


async def _run_deploy(
    job_id: str,
    *,
    name: str,
    install_dir: Path,
    game_port: int,
    rcon_port: int,
    query_port: int,
    max_players: int,
    template_path: Path | None = None,
) -> None:
    try:
        if template_path:
            _append(job_id, f"Creating clean local copy from {template_path}...")
            def ignore(path: str, names: list[str]) -> set[str]:
                rel = Path(path).relative_to(template_path) if Path(path) != template_path else Path('.')
                ignored: set[str] = set()
                if rel == Path('Pal'):
                    ignored.update({n for n in names if n == 'Saved'})
                ignored.update({n for n in names if n in {'Mods', 'Backups', 'logs', '__pycache__'}})
                ignored.update({n for n in names if n.endswith('.log') or n.endswith('.pid')})
                return ignored
            await asyncio.to_thread(shutil.copytree, template_path, install_dir, ignore=ignore, dirs_exist_ok=False)
            _append(job_id, "Server binaries copied locally; saves, mods, logs and runtime data were excluded.")
        else:
            _append(job_id, "Preparing SteamCMD...")
            await steamcmd.install_palserver(install_dir, on_output=lambda line: _append(job_id, line))

        _append(job_id, "Writing initial server settings...")
        # initialize_settings() always reads the copied server's own
        # DefaultPalWorldSettings.ini (or a live ini when appropriate).  The
        # template server path must not be forwarded here: it is not part of
        # the settings service API and the clean clone has already copied the
        # required template file into install_dir.
        palworld_settings.initialize_settings(
            install_dir,
            server_name=name,
            game_port=game_port,
            rcon_port=rcon_port,
            max_players=max_players,
        )

        instance = instance_store.create_instance(
            name=name,
            server_path=str(install_dir),
            source="deployed",
            game_port=game_port,
            rcon_port=rcon_port,
            query_port=query_port,
            use_query_port=True,
        )
        _append(job_id, "Configuring Windows Firewall...")
        try:
            fw = await asyncio.to_thread(firewall.sync_instance, instance)
            created = fw.get("created", [])
            _append(job_id, "Firewall ready." if not created else f"Firewall rules created: {len(created)}")
        except firewall.FirewallError as e:
            _append(job_id, f"WARNING: Firewall setup was not completed: {e.message}")
            _jobs[job_id]["warning"] = e.message
        _append(job_id, "Done.")
        _jobs[job_id]["instanceId"] = instance["id"]
        _jobs[job_id]["status"] = "done"
    except SteamCmdError as e:
        logger.warning("deploy_jobs: job %s failed: %s", job_id, e.message)
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = e.message
    except OSError as e:
        logger.exception("deploy_jobs: job %s failed", job_id)
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(e)
    except Exception as e:
        # A background task must never leave the deployment job in
        # ``running`` forever.  Unexpected programming/runtime errors are
        # surfaced to the polling frontend as a terminal error state.
        logger.exception("deploy_jobs: unexpected failure in job %s", job_id)
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = f"Unexpected deployment error: {e}"
        _append(job_id, f"ERROR: {e}")


def start_deploy(
    *,
    name: str,
    install_dir: Path,
    game_port: int,
    rcon_port: int,
    query_port: int,
    max_players: int,
    template_path: Path | None = None,
) -> str:
    job_id = f"deploy-{uuid.uuid4().hex[:10]}"
    _jobs[job_id] = {"status": "running", "log": [], "error": None, "instanceId": None}
    asyncio.create_task(
        _run_deploy(
            job_id,
            name=name,
            install_dir=install_dir,
            game_port=game_port,
            rcon_port=rcon_port,
            query_port=query_port,
            max_players=max_players,
            template_path=template_path,
        )
    )
    return job_id

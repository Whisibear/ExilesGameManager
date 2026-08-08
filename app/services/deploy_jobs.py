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

from app.games import DEFAULT_GAME_ID, require_deployable_game
from app.games.providers import get_provider_for_game
from app.paths import default_servers_dir
from app.services import activity_log, firewall, instance_store, task_queue
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


def _append(job_id: str, line: str, *, level: str = "info", progress: float | None = None) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    job["log"].append(line)
    if len(job["log"]) > _MAX_LOG_LINES:
        job["log"] = job["log"][-_MAX_LOG_LINES:]
    task_id = job.get("taskId")
    if task_id:
        task_queue.update_external_task(
            task_id,
            message=line,
            progress=progress,
            level=level,
        )


def _fail_job(job_id: str, message: str) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = "error"
    job["error"] = message
    _append(job_id, f"ERROR: {message}", level="error")
    task_id = job.get("taskId")
    if task_id:
        task_queue.finish_external_task(
            task_id,
            success=False,
            message="Server deployment failed.",
            error=message,
        )
    activity_log.log("error", job.get("source") or "Deployment", f"Server deployment failed: {message}")


async def _run_deploy(
    job_id: str,
    *,
    name: str,
    install_dir: Path,
    game_port: int,
    rcon_port: int,
    query_port: int = 8213,
    max_players: int = 32,
    template_path: Path | None = None,
    game_id: str = DEFAULT_GAME_ID,
) -> None:
    try:
        game = require_deployable_game(game_id)
        provider = get_provider_for_game(game.id)
        deployment = provider.deployment
        activity_log.log(
            "info",
            game.label,
            f"Deployment started for server '{name}'.",
        )
        _append(job_id, f"Starting {game.label} deployment...", progress=5)
        ports = {
            "game": game_port,
            "query": query_port,
        }
        if game.id == "palworld":
            ports["restApi"] = rcon_port
        else:
            ports["rcon"] = rcon_port
            pinger = next(
                (item for item in game.port_definitions if item.key == "pinger"),
                None,
            )
            if pinger and pinger.relative_to == "game":
                ports["pinger"] = game_port + pinger.offset

        if template_path:
            _append(job_id, f"Creating clean local copy from {template_path}...", progress=15)

            def ignore(path: str, names: list[str]) -> set[str]:
                return deployment.clone_ignore(
                    template_path,
                    Path(path),
                    names,
                )

            await asyncio.to_thread(
                shutil.copytree,
                template_path,
                install_dir,
                ignore=ignore,
                dirs_exist_ok=False,
            )
            _append(
                job_id,
                "Server binaries copied locally; saves, logs and runtime "
                "data were excluded according to the selected game provider.",
            )
        else:
            _append(job_id, f"Preparing SteamCMD for {game.label}...", progress=15)
            await deployment.install_server(
                install_dir,
                on_output=lambda line: _append(job_id, line),
            )

        _append(job_id, f"Writing initial {game.label} server settings...", progress=65)
        deployment.initialize_server(
            install_dir,
            name=name,
            ports=ports,
            max_players=max_players,
        )

        legacy_game, legacy_management, legacy_query = (
            deployment.legacy_instance_ports(ports)
        )
        instance = instance_store.create_instance(
            name=name,
            server_path=str(install_dir),
            source="deployed",
            game_port=legacy_game,
            rcon_port=legacy_management,
            query_port=legacy_query,
            use_query_port=True,
            game_id=game.id,
            ports=ports,
        )
        task_id = _jobs[job_id].get("taskId")
        if task_id:
            task_queue.bind_external_task_instance(task_id, instance["id"])
        activity_log.log(
            "info",
            instance["name"],
            f"{game.label} instance registered after deployment.",
            instance_id=instance["id"],
        )
        _append(job_id, "Configuring Windows Firewall...", progress=82)
        try:
            fw = await asyncio.to_thread(firewall.sync_instance, instance)
            created = fw.get("created", [])
            _append(job_id, "Firewall ready." if not created else f"Firewall rules created: {len(created)}")
        except firewall.FirewallError as e:
            _append(job_id, f"WARNING: Firewall setup was not completed: {e.message}")
            _jobs[job_id]["warning"] = e.message
        _append(job_id, "Done.", progress=100)
        _jobs[job_id]["instanceId"] = instance["id"]
        _jobs[job_id]["status"] = "done"
        activity_log.log(
            "info",
            instance["name"],
            f"{game.label} deployment completed successfully.",
            instance_id=instance["id"],
        )
        task_id = _jobs[job_id].get("taskId")
        if task_id:
            task_queue.finish_external_task(
                task_id,
                success=True,
                message=f"{game.label} deployment completed successfully.",
            )
    except SteamCmdError as e:
        logger.warning("deploy_jobs: job %s failed: %s", job_id, e.message)
        _fail_job(job_id, e.message)
    except OSError as e:
        logger.exception("deploy_jobs: job %s failed", job_id)
        _fail_job(job_id, str(e))
    except Exception as e:
        # A background task must never leave the deployment job in
        # ``running`` forever.  Unexpected programming/runtime errors are
        # surfaced to the polling frontend as a terminal error state.
        logger.exception("deploy_jobs: unexpected failure in job %s", job_id)
        _fail_job(job_id, f"Unexpected deployment error: {e}")


def start_deploy(
    *,
    name: str,
    install_dir: Path,
    game_port: int,
    rcon_port: int,
    query_port: int,
    max_players: int,
    template_path: Path | None = None,
    game_id: str = DEFAULT_GAME_ID,
) -> str:
    job_id = f"deploy-{uuid.uuid4().hex[:10]}"
    task_id = task_queue.create_external_task(
        "server.deploy",
        title=f"Deploy {name}",
        message=f"Preparing deployment for {name}",
        priority=70,
    )
    _jobs[job_id] = {
        "status": "running",
        "log": [],
        "error": None,
        "instanceId": None,
        "taskId": task_id,
        "source": name,
    }
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
            game_id=game_id,
        )
    )
    return job_id

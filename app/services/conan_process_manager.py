from __future__ import annotations

import logging
import os
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import psutil

from app.games import executable_path, require_game
from app.services import activity_log
from app.services.windows_subprocess import hidden_process_kwargs

logger = logging.getLogger("egm.conan_process_manager")

_STARTUP_GRACE_SECONDS = 20
_PROCESS_NAMES = {
    "conansandboxserver-win64-shipping.exe",
    "conansandboxserver.exe",
}

_lock = threading.Lock()
_processes: dict[str, subprocess.Popen] = {}
_started_at: dict[str, float] = {}
_stopping: set[str] = set()
_recent_intentional_stop: dict[str, float] = {}


class ConanProcessError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _path_key(path: Path | str) -> str:
    try:
        return os.path.normcase(str(Path(path).resolve()))
    except OSError:
        return os.path.normcase(str(path))


def _path_is_inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([root, _path_key(path)]) == root
    except (OSError, ValueError):
        return False


def executable_for(instance: dict[str, Any]) -> Path:
    game = require_game(str(instance.get("gameId") or ""))
    root = Path(instance["serverPath"])
    exe = executable_path(game, root)
    if exe is None:
        expected = ", ".join(game.executable_candidates)
        raise ConanProcessError(
            f"{game.label} dedicated-server executable was not found "
            f"under '{root}'. Expected one of: {expected}"
        )
    return exe


def build_launch_args(instance: dict[str, Any]) -> list[str]:
    exe = executable_for(instance)
    ports = dict(instance.get("ports") or {})
    game_port = int(ports.get("game") or instance.get("gamePort") or 7777)
    query_port = int(
        ports.get("query") or instance.get("queryPort") or 27015
    )
    rcon_port = int(
        ports.get("rcon") or instance.get("rconPort") or 25575
    )

    args = [
        str(exe),
        f"-Port={game_port}",
        f"-QueryPort={query_port}",
        f"-RconPort={rcon_port}",
    ]
    if exe.name.lower() == "conansandboxserver-win64-shipping.exe":
        args.append("-log")

    multihome = str(instance.get("multihome") or "").strip()
    if multihome:
        args.append(f"-MULTIHOME={multihome}")

    extra = instance.get("conanLaunchArgs")
    if isinstance(extra, list):
        args.extend(
            str(value).strip()
            for value in extra
            if str(value).strip()
        )

    return args


def _safe_process_tree(pid: int) -> list[psutil.Process]:
    try:
        root = psutil.Process(pid)
    except psutil.Error:
        return []
    try:
        return [root, *root.children(recursive=True)]
    except psutil.Error:
        return [root]


def _process_matches_instance(
    proc: psutil.Process,
    server_root: str,
) -> bool:
    try:
        name = (proc.name() or "").lower()
    except psutil.Error:
        return False

    if name not in _PROCESS_NAMES:
        return False

    for getter in (proc.exe, proc.cwd):
        try:
            value = getter()
        except psutil.Error:
            continue
        if value and _path_is_inside(value, server_root):
            return True

    try:
        command_line = proc.cmdline()
    except psutil.Error:
        command_line = []

    return any(
        _path_is_inside(part, server_root)
        for part in command_line
        if part
    )


def instance_processes(
    instance: dict[str, Any],
) -> list[psutil.Process]:
    seen: set[int] = set()
    processes: list[psutil.Process] = []

    tracked = _processes.get(instance["id"])
    if tracked and tracked.poll() is None:
        for proc in _safe_process_tree(tracked.pid):
            if proc.pid not in seen:
                seen.add(proc.pid)
                processes.append(proc)

    server_root = _path_key(instance["serverPath"])
    for proc in psutil.process_iter():
        if proc.pid in seen:
            continue
        if _process_matches_instance(proc, server_root):
            seen.add(proc.pid)
            processes.append(proc)

    return processes


def is_running(instance: dict[str, Any]) -> bool:
    return bool(instance_processes(instance))


def mark_intentional_stop(instance_id: str) -> None:
    with _lock:
        _stopping.add(instance_id)
        _recent_intentional_stop[instance_id] = time.time()


def was_intentionally_stopped_recently(
    instance_id: str,
    seconds: float = 60.0,
) -> bool:
    stopped_at = _recent_intentional_stop.get(instance_id)
    return (
        stopped_at is not None
        and (time.time() - stopped_at) <= seconds
    )


def start(instance: dict[str, Any]) -> None:
    instance_id = instance["id"]

    with _lock:
        if instance_processes(instance):
            raise ConanProcessError(
                "This Conan Exiles server is already running."
            )

        args = build_launch_args(instance)
        exe = Path(args[0])

        # The root ConanSandboxServer.exe intentionally presents Funcom's
        # small "close this window to shutdown" launcher window. Do not hide
        # that launcher; simply omit -log so it does not become the large
        # scrolling output console. A direct Shipping fallback remains fully
        # hidden because it has no launcher UI of its own.
        if exe.name.lower() == "conansandboxserver.exe":
            process_kwargs: dict[str, Any] = {}
        else:
            process_kwargs = hidden_process_kwargs()
        if os.name == "nt":
            process_kwargs["creationflags"] = (
                int(process_kwargs.get("creationflags", 0))
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )

        try:
            proc = subprocess.Popen(
                args,
                cwd=str(exe.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                **process_kwargs,
            )
        except OSError as exc:
            raise ConanProcessError(
                f"Could not start Conan Exiles: {exc}"
            ) from exc

        _processes[instance_id] = proc
        _started_at[instance_id] = time.time()
        _stopping.discard(instance_id)
        _recent_intentional_stop.pop(instance_id, None)

    ports = dict(instance.get("ports") or {})
    game_port = ports.get("game") or instance.get("gamePort") or 7777
    query_port = (
        ports.get("query") or instance.get("queryPort") or 27015
    )
    rcon_port = ports.get("rcon") or instance.get("rconPort") or 25575

    logger.info(
        "conan_process_manager: started %r "
        "(pid=%s, game=%s, query=%s, rcon=%s)",
        instance["name"],
        proc.pid,
        game_port,
        query_port,
        rcon_port,
    )
    activity_log.log(
        "info",
        instance["name"],
        (
            "Conan Exiles server started "
            f"(game {game_port}, query {query_port}, "
            f"RCON {rcon_port})."
        ),
    )


def _terminate_tree(
    proc: subprocess.Popen,
    *,
    timeout: float,
) -> None:
    tree = _safe_process_tree(proc.pid)

    if os.name == "nt":
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except (OSError, ValueError):
            pass
    else:
        try:
            proc.terminate()
        except OSError:
            pass

    deadline = time.time() + timeout
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.25)

    alive = []
    for process in tree:
        try:
            if process.is_running():
                alive.append(process)
        except psutil.Error:
            continue

    if alive:
        for process in alive:
            try:
                process.kill()
            except psutil.Error:
                pass
        psutil.wait_procs(alive, timeout=10)


def stop(
    instance: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> None:
    instance_id = instance["id"]
    mark_intentional_stop(instance_id)

    with _lock:
        tracked = _processes.get(instance_id)

    processes = instance_processes(instance)
    if not processes:
        with _lock:
            _processes.pop(instance_id, None)
            _started_at.pop(instance_id, None)
            _stopping.discard(instance_id)
        return

    if tracked and tracked.poll() is None:
        logger.info(
            "conan_process_manager: stopping tracked pid=%s",
            tracked.pid,
        )
        _terminate_tree(tracked, timeout=timeout)
    else:
        for process in processes:
            try:
                process.terminate()
            except psutil.Error:
                continue
        _, alive = psutil.wait_procs(processes, timeout=timeout)
        for process in alive:
            try:
                process.kill()
            except psutil.Error:
                pass
        if alive:
            psutil.wait_procs(alive, timeout=10)

    with _lock:
        _processes.pop(instance_id, None)
        _started_at.pop(instance_id, None)
        _stopping.discard(instance_id)

    logger.info(
        "conan_process_manager: stopped %r",
        instance.get("name", instance_id),
    )
    activity_log.log(
        "info",
        instance.get("name", instance_id),
        "Conan Exiles server stopped.",
    )


def restart(instance: dict[str, Any]) -> None:
    stop(instance)
    start(instance)


def _cpu_ram(
    processes: list[psutil.Process],
) -> tuple[float, float]:
    cpu_percent = 0.0
    ram_bytes = 0

    for process in processes:
        try:
            cpu_percent += process.cpu_percent(interval=0.05)
            ram_bytes += process.memory_info().rss
        except psutil.Error:
            continue

    cpu_percent /= psutil.cpu_count() or 1
    return cpu_percent, ram_bytes / (1024**3)


def get_status(instance: dict[str, Any]) -> dict[str, Any]:
    instance_id = instance["id"]

    if instance_id in _stopping:
        return {
            "state": "stopping",
            "uptimeSeconds": 0,
            "cpuPercent": 0.0,
            "ramUsedGB": 0.0,
        }

    processes = instance_processes(instance)
    if not processes:
        with _lock:
            _processes.pop(instance_id, None)
            _started_at.pop(instance_id, None)
        return {
            "state": "offline",
            "uptimeSeconds": 0,
            "cpuPercent": 0.0,
            "ramUsedGB": 0.0,
        }

    started_at = _started_at.get(instance_id)
    if started_at is None:
        created = []
        for process in processes:
            try:
                created.append(process.create_time())
            except psutil.Error:
                continue
        started_at = min(created) if created else time.time()
        _started_at[instance_id] = started_at

    uptime = max(0.0, time.time() - started_at)
    cpu_percent, ram_gb = _cpu_ram(processes)

    return {
        "state": (
            "starting"
            if uptime < _STARTUP_GRACE_SECONDS
            else "online"
        ),
        "uptimeSeconds": int(uptime),
        "cpuPercent": round(cpu_percent, 1),
        "ramUsedGB": round(ram_gb, 2),
    }

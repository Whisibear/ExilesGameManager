from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import psutil

from app.services import instance_store, process_manager

_lock = threading.Lock()
_last_net: tuple[float, int, int] | None = None
_last_disk: tuple[float, int, int] | None = None


def _rates() -> dict[str, float]:
    global _last_net, _last_disk
    now = time.time()
    net = psutil.net_io_counters()
    disk = psutil.disk_io_counters()
    with _lock:
        net_up = net_down = disk_read = disk_write = 0.0
        if _last_net:
            t, sent, recv = _last_net
            elapsed = max(now - t, 0.001)
            net_up = max(0.0, (net.bytes_sent - sent) / elapsed)
            net_down = max(0.0, (net.bytes_recv - recv) / elapsed)
        if disk and _last_disk:
            t, read, write = _last_disk
            elapsed = max(now - t, 0.001)
            disk_read = max(0.0, (disk.read_bytes - read) / elapsed)
            disk_write = max(0.0, (disk.write_bytes - write) / elapsed)
        _last_net = (now, net.bytes_sent, net.bytes_recv)
        if disk:
            _last_disk = (now, disk.read_bytes, disk.write_bytes)
    return {
        "networkUploadBytesPerSecond": net_up,
        "networkDownloadBytesPerSecond": net_down,
        "diskReadBytesPerSecond": disk_read,
        "diskWriteBytesPerSecond": disk_write,
    }


def _disk_usage(path: Path) -> dict[str, float]:
    try:
        usage = psutil.disk_usage(str(path))
    except OSError:
        usage = psutil.disk_usage(str(Path.cwd()))
    return {
        "diskUsedBytes": float(usage.used),
        "diskTotalBytes": float(usage.total),
        "diskPercent": float(usage.percent),
    }


def active_snapshot() -> dict[str, Any]:
    instance = instance_store.get_active()
    if not instance:
        raise ValueError("No server selected.")
    vm = psutil.virtual_memory()
    status = process_manager.get_status(instance["id"])
    return {
        "instanceId": instance["id"],
        "instanceName": instance["name"],
        "serverPath": instance["serverPath"],
        "state": status["state"],
        "uptimeSeconds": status["uptimeSeconds"],
        "serverCpuPercent": status["cpuPercent"],
        "serverRamBytes": int(float(status["ramUsedGB"]) * 1024**3),
        "systemCpuPercent": psutil.cpu_percent(interval=None),
        "systemRamUsedBytes": int(vm.used),
        "systemRamTotalBytes": int(vm.total),
        "systemRamPercent": float(vm.percent),
        "logicalCpuCount": psutil.cpu_count(logical=True) or 0,
        "physicalCpuCount": psutil.cpu_count(logical=False) or 0,
        **_disk_usage(Path(instance["serverPath"])),
        **_rates(),
        "sampledAt": time.time(),
    }


def all_instances_snapshot() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in instance_store.list_instances():
        status = process_manager.get_status(instance["id"])
        rows.append({
            "instanceId": instance["id"],
            "instanceName": instance["name"],
            "state": status["state"],
            "uptimeSeconds": status["uptimeSeconds"],
            "serverCpuPercent": status["cpuPercent"],
            "serverRamBytes": int(float(status["ramUsedGB"]) * 1024**3),
            "gamePort": instance_store.resolve_game_port(instance),
        })
    return rows

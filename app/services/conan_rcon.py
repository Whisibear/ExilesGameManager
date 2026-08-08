from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services import conan_settings, source_rcon

_DEFAULT_TIMEOUT = 5.0


def sanitize_command_for_log(command: str) -> str:
    cleaned = str(command).replace("\r", " ").replace("\n", " ").strip()
    if not cleaned:
        return "<empty>"
    head = cleaned.split(maxsplit=1)[0].casefold()
    if any(token in head for token in ("password", "passwd", "secret", "token", "auth")):
        return f"{cleaned.split(maxsplit=1)[0]} <redacted>"
    return cleaned[:512]


class ConanRconError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True, slots=True)
class RconEndpoint:
    host: str
    port: int
    password: str


def _settings(instance: dict[str, Any]) -> dict[str, Any]:
    return {
        field["key"]: field["value"]
        for field in conan_settings.read_all_settings(Path(instance["serverPath"]))
    }


def endpoint_for(instance: dict[str, Any]) -> RconEndpoint:
    values = _settings(instance)
    enabled = values.get("RconEnabled", True)
    if enabled is False or str(enabled).strip().casefold() in {"0", "false", "no", "off"}:
        raise ConanRconError("RCON is disabled for this Conan Exiles server.")

    ports = dict(instance.get("ports") or {})
    runtime_port = int(ports.get("rcon") or instance.get("rconPort") or 0)
    configured_port = int(values.get("RconPort") or 25575)
    port = runtime_port or configured_port
    if runtime_port and configured_port and runtime_port != configured_port:
        raise ConanRconError(
            f"Conan RCON port mismatch: EGM uses {runtime_port}, but Game.ini contains {configured_port}. "
            "Save the Conan server settings or make both values identical before using RCON."
        )

    password = str(values.get("RconPassword") or "")
    if not password:
        raise ConanRconError("No RCON password is configured for this Conan Exiles server.")

    return RconEndpoint("127.0.0.1", port, password)


def execute_sync(
    instance: dict[str, Any],
    command: str,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> str:
    endpoint = endpoint_for(instance)
    generic_endpoint = source_rcon.SourceRconEndpoint(endpoint.host, endpoint.port, endpoint.password)
    try:
        return source_rcon.execute_mcrcon(generic_endpoint, command, timeout=timeout)
    except source_rcon.SourceRconError as exc:
        message = str(exc)
        if message.startswith("Could not communicate with RCON on "):
            message = message.replace("Could not communicate with RCON on ", "Could not communicate with Conan RCON on ", 1)
        raise ConanRconError(message) from exc


def check_ready_sync(
    instance: dict[str, Any],
    *,
    timeout: float = 2.0,
) -> dict[str, Any]:
    del timeout
    endpoint = endpoint_for(instance)
    return {"ready": True, "host": endpoint.host, "port": endpoint.port, "mode": "configured"}


async def execute(
    instance: dict[str, Any],
    command: str,
    *,
    timeout: float = _DEFAULT_TIMEOUT,
) -> str:
    return await asyncio.to_thread(execute_sync, instance, command, timeout=timeout)


async def check_ready(instance: dict[str, Any], *, timeout: float = 2.0) -> dict[str, Any]:
    return await asyncio.to_thread(check_ready_sync, instance, timeout=timeout)


async def broadcast(instance: dict[str, Any], message: str) -> str:
    cleaned = str(message).replace("\r", " ").replace("\n", " ").strip()
    if not cleaned:
        raise ConanRconError("Broadcast message must not be empty.")
    return await execute(instance, f"Broadcast {cleaned}")


async def list_players(instance: dict[str, Any]) -> str:
    return await execute(instance, "ShowPlayers")

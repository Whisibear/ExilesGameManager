from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from app.games import require_game
from app.games.providers.base import (
    DeploymentProvider,
    NetworkProvider,
    GameProvider,
    ServerControlProvider,
    ServerSettingsProvider,
)
from app.services import (
    instance_store,
    palworld_rest,
    palworld_settings,
    process_manager,
    server_update,
    steamcmd,
)
from app.services.palworld_rest import PalworldRestError

logger = logging.getLogger("egm.games.palworld")


class PalworldControlProvider(ServerControlProvider):
    game_id = "palworld"

    def read_max_players(self, instance: dict[str, Any]) -> int:
        return (
            palworld_settings.read_max_players(Path(instance["serverPath"]))
            or 32
        )

    async def enrich_status(
        self,
        instance: dict[str, Any],
        status: dict[str, Any],
    ) -> dict[str, Any]:
        if status["state"] not in ("online", "starting"):
            return status
        try:
            metrics, info = await asyncio.gather(
                palworld_rest.metrics(instance),
                palworld_rest.info(instance),
            )
        except PalworldRestError as exc:
            logger.info(
                "REST status enrichment skipped for %s (%s)",
                instance["name"],
                exc.message,
            )
            return status
        return {
            **status,
            "tickRateMs": metrics.get("serverframetime"),
            "playersOnline": metrics.get("currentplayernum") or 0,
            "maxPlayers": metrics.get("maxplayernum") or status["maxPlayers"],
            "serverVersion": info.get("version") or status["serverVersion"],
            "uptimeSeconds": metrics.get("uptime") or status["uptimeSeconds"],
        }

    async def start(self, instance: dict[str, Any]) -> None:
        await asyncio.to_thread(process_manager.start, instance)

    async def stop(self, instance: dict[str, Any]) -> None:
        process_manager.mark_intentional_stop(instance["id"])
        try:
            await palworld_rest.shutdown(instance, 1, "Server stopping.")
            await asyncio.sleep(3)
        except PalworldRestError as exc:
            logger.info(
                "REST shutdown skipped for %s (%s)",
                instance["name"],
                exc.message,
            )
        await asyncio.to_thread(process_manager.stop, instance["id"])

    async def restart(self, instance: dict[str, Any]) -> None:
        process_manager.mark_intentional_stop(instance["id"])
        try:
            await palworld_rest.shutdown(instance, 1, "Server restarting.")
            await asyncio.sleep(3)
        except PalworldRestError as exc:
            logger.info(
                "REST restart shutdown skipped for %s (%s)",
                instance["name"],
                exc.message,
            )
        await asyncio.to_thread(process_manager.stop, instance["id"])
        await asyncio.to_thread(process_manager.start, instance)

    async def save(self, instance: dict[str, Any]) -> str:
        await palworld_rest.save(instance)
        return process_manager.record_save(instance["id"])

    async def broadcast(
        self,
        instance: dict[str, Any],
        message: str,
    ) -> None:
        await palworld_rest.announce(instance, message)

    async def shutdown(
        self,
        instance: dict[str, Any],
        message: str,
    ) -> None:
        process_manager.mark_intentional_stop(instance["id"])
        try:
            await palworld_rest.shutdown(instance, 1, message)
            await asyncio.sleep(3)
        except PalworldRestError as exc:
            logger.info(
                "REST countdown shutdown skipped for %s (%s)",
                instance["name"],
                exc.message,
            )
        await asyncio.to_thread(process_manager.stop, instance["id"])

    async def check_update(
        self,
        instance: dict[str, Any],
    ) -> dict[str, Any]:
        return await server_update.check_for_update(instance)

    def start_update(self, instance: dict[str, Any]) -> str:
        return server_update.start_update(instance)

    def get_update_job(self, job_id: str) -> dict[str, Any] | None:
        return server_update.get_job(job_id)


class PalworldSettingsProvider(ServerSettingsProvider):
    game_id = "palworld"
    credential_fields = frozenset({"AdminPassword", "ServerPassword"})
    restricted_fields = frozenset(palworld_settings.LOCAL_API_SETTING_KEYS)

    def read_fields(
        self,
        instance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return palworld_settings.read_all_settings(
            Path(instance["serverPath"])
        )

    def write_fields(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        palworld_settings.write_settings(
            Path(instance["serverPath"]),
            values,
        )

    def synchronize_instance_metadata(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        if "PublicPort" in values:
            instance_store.update_game_port(
                instance["id"],
                int(values["PublicPort"]),
            )


class PalworldNetworkProvider(NetworkProvider):
    game_id = "palworld"
    @property
    def port_definitions(self): return require_game(self.game_id).port_definitions
    def firewall_enabled(self, definition, instance, *, include_management=True):
        if not definition.firewall: return False
        if definition.key == "query" and not bool(instance.get("useQueryPort")): return False
        if definition.key == "restApi" and not include_management: return False
        return True


class PalworldDeploymentProvider(DeploymentProvider):
    game_id = "palworld"

    @property
    def steam_install_spec(self):
        definition = require_game(self.game_id).steam_install
        if definition is None:
            raise RuntimeError("Palworld Steam install metadata is missing.")
        return definition

    async def install_server(
        self,
        install_dir: Path,
        on_output=None,
    ) -> None:
        await steamcmd.install_from_definition(
            install_dir,
            self.steam_install_spec,
            on_output=on_output,
        )

    def clone_ignore(
        self,
        template_root: Path,
        current_path: Path,
        names: list[str],
    ) -> set[str]:
        relative = (
            current_path.relative_to(template_root)
            if current_path != template_root
            else Path(".")
        )
        ignored: set[str] = set()
        if relative == Path("Pal"):
            ignored.update(name for name in names if name == "Saved")
        ignored.update(
            name
            for name in names
            if name in {"Mods", "Backups", "logs", "__pycache__"}
        )
        ignored.update(
            name
            for name in names
            if name.endswith(".log") or name.endswith(".pid")
        )
        return ignored

    def initialize_server(
        self,
        install_dir: Path,
        *,
        name: str,
        ports: dict[str, int],
        max_players: int,
    ) -> None:
        palworld_settings.initialize_settings(
            install_dir,
            server_name=name,
            game_port=ports["game"],
            rcon_port=ports["restApi"],
            max_players=max_players,
        )

    def legacy_instance_ports(
        self,
        ports: dict[str, int],
    ) -> tuple[int, int, int]:
        return ports["game"], ports["restApi"], ports["query"]


class PalworldProvider(GameProvider):
    game_id = "palworld"

    def __init__(self) -> None:
        self.control = PalworldControlProvider()
        self.settings = PalworldSettingsProvider()
        self.deployment = PalworldDeploymentProvider()
        self.network = PalworldNetworkProvider()

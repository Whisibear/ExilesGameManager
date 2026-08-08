from __future__ import annotations

from pathlib import Path
from typing import Any

from app.games.providers.base import (
    DeploymentProvider,
    NetworkProvider,
    GameProvider,
    ServerControlProvider,
    ServerSettingsProvider,
)
from app.games import require_game
from app.services import (
    conan_process_manager,
    conan_rcon,
    conan_settings,
    instance_store,
    server_update,
    steamcmd,
)


class ConanProviderNotImplementedError(RuntimeError):
    pass


def _not_available(edition: str) -> ConanProviderNotImplementedError:
    return ConanProviderNotImplementedError(
        f"Conan Exiles {edition.title()} is registered, but installation, "
        "RCON, settings and process control are not enabled in this build."
    )


class ConanControlProvider(ServerControlProvider):
    def __init__(self, game_id: str, edition: str) -> None:
        self.game_id = game_id
        self.edition = edition

    def read_max_players(self, instance: dict[str, Any]) -> int:
        return conan_settings.read_max_players(
            Path(instance["serverPath"])
        )

    async def enrich_status(
        self,
        instance: dict[str, Any],
        status: dict[str, Any],
    ) -> dict[str, Any]:
        runtime = conan_process_manager.get_status(instance)
        return {
            **status,
            "state": runtime["state"],
            "uptimeSeconds": runtime["uptimeSeconds"],
            "cpuPercent": runtime["cpuPercent"],
            "ramUsedGB": runtime["ramUsedGB"],
        }

    async def start(self, instance: dict[str, Any]) -> None:
        conan_process_manager.start(instance)

    async def stop(self, instance: dict[str, Any]) -> None:
        conan_process_manager.stop(instance)

    async def restart(self, instance: dict[str, Any]) -> None:
        conan_process_manager.restart(instance)

    async def save(self, instance: dict[str, Any]) -> str:
        raise ConanProviderNotImplementedError(
            "Manual Conan world-save control is not exposed by this build."
        )

    async def broadcast(
        self,
        instance: dict[str, Any],
        message: str,
    ) -> None:
        await conan_rcon.broadcast(instance, message)

    async def shutdown(
        self,
        instance: dict[str, Any],
        message: str,
    ) -> None:
        conan_process_manager.stop(instance)

    async def check_update(
        self,
        instance: dict[str, Any],
    ) -> dict[str, Any]:
        return await server_update.check_for_update(instance)

    def start_update(self, instance: dict[str, Any]) -> str:
        return server_update.start_update(instance)

    def get_update_job(self, job_id: str) -> dict[str, Any] | None:
        return server_update.get_job(job_id)

    def _steam_install_spec(self):
        definition = require_game(self.game_id).steam_install
        if definition is None:
            raise ConanProviderNotImplementedError(
                "Conan Steam installation metadata is missing."
            )
        return definition


class ConanSettingsProvider(ServerSettingsProvider):
    credential_fields = frozenset(
        {"AdminPassword", "RconPassword", "ServerPassword"}
    )
    restricted_fields = frozenset()

    def __init__(self, game_id: str, edition: str) -> None:
        self.game_id = game_id
        self.edition = edition

    def read_fields(
        self,
        instance: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return conan_settings.read_all_settings(Path(instance["serverPath"]))

    def write_fields(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        conan_settings.write_settings(Path(instance["serverPath"]), values)

    def synchronize_instance_metadata(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        relevant = {
            key: int(values[key])
            for key in ("GamePort", "QueryPort", "RconPort")
            if key in values
        }
        if relevant:
            instance_store.update_network_ports(
                instance["id"],
                game_id=self.game_id,
                **relevant,
            )


class ConanNetworkProvider(NetworkProvider):
    def __init__(self, game_id: str): self.game_id = game_id
    @property
    def port_definitions(self): return require_game(self.game_id).port_definitions


class ConanDeploymentProvider(DeploymentProvider):
    def __init__(self, game_id: str, edition: str) -> None:
        self.game_id = game_id
        self.edition = edition

    @property
    def steam_install_spec(self):
        definition = require_game(self.game_id).steam_install
        if definition is None:
            raise ConanProviderNotImplementedError(
                f"{require_game(self.game_id).label} has no Steam server "
                "application configured."
            )
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
        ignored: set[str] = set()
        relative = (
            current_path.relative_to(template_root)
            if current_path != template_root
            else Path(".")
        )
        if relative == Path("ConanSandbox"):
            ignored.update(name for name in names if name == "Saved")
        ignored.update(
            name
            for name in names
            if name in {"Backups", "logs", "__pycache__"}
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
        conan_settings.initialize_settings(
            install_dir,
            server_name=name,
            ports=ports,
            max_players=max_players,
        )

    def legacy_instance_ports(
        self,
        ports: dict[str, int],
    ) -> tuple[int, int, int]:
        return ports["game"], ports["rcon"], ports["query"]


class ConanProvider(GameProvider):
    def __init__(self, game_id: str, edition: str) -> None:
        self.game_id = game_id
        self.edition = edition
        self.control = ConanControlProvider(game_id, edition)
        self.settings = ConanSettingsProvider(game_id, edition)
        self.deployment = ConanDeploymentProvider(game_id, edition)
        self.network = ConanNetworkProvider(game_id)

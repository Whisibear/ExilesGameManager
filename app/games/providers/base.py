from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from collections.abc import Callable
from typing import Any

from app.games.models import PortDefinition, SteamInstallDefinition


class ServerControlProvider(ABC):
    game_id: str

    @abstractmethod
    def read_max_players(self, instance: dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def enrich_status(
        self,
        instance: dict[str, Any],
        status: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def start(self, instance: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self, instance: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def restart(self, instance: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, instance: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def broadcast(self, instance: dict[str, Any], message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self, instance: dict[str, Any], message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def check_update(self, instance: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def start_update(self, instance: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_update_job(self, job_id: str) -> dict[str, Any] | None:
        raise NotImplementedError


class ServerSettingsProvider(ABC):
    game_id: str
    credential_fields: frozenset[str]
    restricted_fields: frozenset[str]

    @abstractmethod
    def read_fields(self, instance: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def write_fields(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    def synchronize_instance_metadata(
        self,
        instance: dict[str, Any],
        values: dict[str, Any],
    ) -> None:
        return None


class NetworkProvider(ABC):
    game_id: str

    @property
    @abstractmethod
    def port_definitions(self) -> tuple[PortDefinition, ...]:
        raise NotImplementedError

    def resolve_ports(self, instance: dict[str, Any]) -> dict[str, int]:
        raw = instance.get("ports")
        if isinstance(raw, dict):
            result = {}
            for key, value in raw.items():
                try: port = int(value)
                except (TypeError, ValueError): continue
                if 1 <= port <= 65535: result[str(key)] = port
            if result: return result
        result = {}
        legacy_map = {"game":"gamePort","restApi":"rconPort","rcon":"rconPort","query":"queryPort"}
        for definition in self.port_definitions:
            legacy_key = legacy_map.get(definition.key)
            if not legacy_key: continue
            try: port = int(instance.get(legacy_key))
            except (TypeError, ValueError): continue
            if 1 <= port <= 65535: result[definition.key] = port
        for definition in self.port_definitions:
            if definition.relative_to and definition.relative_to in result and definition.key not in result:
                result[definition.key] = result[definition.relative_to] + definition.offset
        return result

    def firewall_enabled(self, definition: PortDefinition, instance: dict[str, Any], *, include_management: bool = True) -> bool:
        return definition.firewall


class DeploymentProvider(ABC):
    game_id: str

    @property
    @abstractmethod
    def steam_install_spec(self) -> SteamInstallDefinition:
        raise NotImplementedError

    @abstractmethod
    async def install_server(
        self,
        install_dir: Path,
        on_output: Callable[[str], None] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def clone_ignore(
        self,
        template_root: Path,
        current_path: Path,
        names: list[str],
    ) -> set[str]:
        raise NotImplementedError

    @abstractmethod
    def initialize_server(
        self,
        install_dir: Path,
        *,
        name: str,
        ports: dict[str, int],
        max_players: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def legacy_instance_ports(
        self,
        ports: dict[str, int],
    ) -> tuple[int, int, int]:
        raise NotImplementedError


class GameProvider(ABC):
    game_id: str
    control: ServerControlProvider
    settings: ServerSettingsProvider
    deployment: DeploymentProvider
    network: NetworkProvider

    @property
    def server_path_type(self) -> type[Path]:
        return Path

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Literal

GameAvailability = Literal["available", "planned"]
GameEdition = Literal["standard", "enhanced", "legacy"]
PortProtocol = Literal["TCP", "UDP"]

@dataclass(frozen=True, slots=True)
class PortDefinition:
    key: str
    label: str
    default: int
    protocol: PortProtocol
    configurable: bool = True
    relative_to: str | None = None
    offset: int = 0
    firewall: bool = True
    def to_dict(self) -> dict[str, object]:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class SteamInstallDefinition:
    app_id: int
    executable_candidates: tuple[str, ...]
    branch: str | None = None
    validate: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GameCapabilities:
    server_control: bool
    server_settings: bool
    steam_workshop: bool
    nexus_mods: bool
    live_console: bool
    rcon: bool
    rest_api: bool
    ue4ss: bool
    firewall_management: bool
    backups: bool
    performance_monitoring: bool
    def to_dict(self) -> dict[str, bool]:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class GameDefinition:
    id: str
    family: str
    edition: GameEdition
    label: str
    short_label: str
    availability: GameAvailability
    steam_server_app_id: int | None
    steam_workshop_app_id: int | None
    steam_branch: str | None
    executable_candidates: tuple[str, ...]
    port_definitions: tuple[PortDefinition, ...]
    capabilities: GameCapabilities
    @property
    def steam_install(self) -> SteamInstallDefinition | None:
        if self.steam_server_app_id is None:
            return None
        return SteamInstallDefinition(
            app_id=self.steam_server_app_id,
            executable_candidates=self.executable_candidates,
            branch=self.steam_branch,
        )

    @property
    def deployable(self) -> bool:
        return self.availability == "available"
    @property
    def default_ports(self) -> dict[str, int]:
        return {item.key: item.default for item in self.port_definitions}
    def to_public_dict(self) -> dict[str, object]:
        return {
            "id": self.id, "family": self.family, "edition": self.edition,
            "label": self.label, "shortLabel": self.short_label,
            "availability": self.availability, "deployable": self.deployable,
            "steamServerAppId": self.steam_server_app_id,
            "steamWorkshopAppId": self.steam_workshop_app_id,
            "steamBranch": self.steam_branch,
            "executableNames": list(self.executable_candidates),
            "defaultPorts": self.default_ports,
            "portDefinitions": [item.to_dict() for item in self.port_definitions],
            "capabilities": self.capabilities.to_dict(),
        }

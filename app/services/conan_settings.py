from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import secrets
from typing import Any


WINDOWS_SERVER_RELATIVE = Path("ConanSandbox") / "Saved" / "Config" / "WindowsServer"
ENGINE_INI = "Engine.ini"
GAME_INI = "Game.ini"
SERVER_SETTINGS_INI = "ServerSettings.ini"


@dataclass(frozen=True, slots=True)
class ConanSettingDefinition:
    key: str
    file_name: str
    section: str
    ini_key: str
    field_type: str
    default: Any
    label: str
    group: str
    description: str
    sensitive: bool = False
    popular: bool = True
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    restart_required: bool = True

    def public_field(self, value: Any) -> dict[str, Any]:
        return {
            "key": self.key,
            "type": self.field_type,
            "value": value,
            "label": self.label,
            "description": self.description,
            "help": self.description,
            "group": self.group,
            "options": None,
            "sensitive": self.sensitive,
            "popular": self.popular,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
            "restartRequired": self.restart_required,
            "sourceFile": self.file_name,
            "sourceSection": self.section,
            "sourceKey": self.ini_key,
        }


DEFINITIONS: tuple[ConanSettingDefinition, ...] = (
    ConanSettingDefinition("ServerName", ENGINE_INI, "OnlineSubsystem", "ServerName", "string", "Exiles Game Manager Conan Server", "Server Name", "Server & Network", "Public name shown for the Conan Exiles server."),
    ConanSettingDefinition("ServerPassword", ENGINE_INI, "OnlineSubsystem", "ServerPassword", "string", "", "Server Password", "Security", "Optional password required to join the server.", sensitive=True),
    ConanSettingDefinition("GamePort", ENGINE_INI, "URL", "Port", "int", 7777, "Game Port", "Server & Network", "Primary UDP game port.", minimum=1, maximum=65535),
    ConanSettingDefinition("QueryPort", ENGINE_INI, "OnlineSubsystemNull", "GameServerQueryPort", "int", 27015, "Query Port", "Server & Network", "UDP server-query port.", minimum=1, maximum=65535),
    ConanSettingDefinition("NetServerMaxTickRate", ENGINE_INI, "/Script/OnlineSubsystemUtils.IpNetDriver", "NetServerMaxTickRate", "int", 30, "Server Tick Rate", "Performance", "Maximum server network tick rate.", popular=False, minimum=1, maximum=120),
    ConanSettingDefinition("MaxPlayers", GAME_INI, "/Script/Engine.GameSession", "MaxPlayers", "int", 32, "Maximum Players", "Server & Network", "Maximum number of simultaneous players.", minimum=1, maximum=70),
    ConanSettingDefinition("RconEnabled", GAME_INI, "RconPlugin", "RconEnabled", "bool", True, "RCON Enabled", "RCON", "Enables Conan Exiles remote administration."),
    ConanSettingDefinition("RconPort", GAME_INI, "RconPlugin", "RconPort", "int", 25575, "RCON Port", "RCON", "TCP port used by RCON.", minimum=1, maximum=65535),
    ConanSettingDefinition("RconPassword", GAME_INI, "RconPlugin", "RconPassword", "string", "", "RCON Password", "RCON", "Password used for RCON authentication.", sensitive=True),
    ConanSettingDefinition("AdminPassword", SERVER_SETTINGS_INI, "ServerSettings", "AdminPassword", "string", "", "Admin Password", "Security", "Password used to become an in-game administrator.", sensitive=True),
    ConanSettingDefinition("PVPEnabled", SERVER_SETTINGS_INI, "ServerSettings", "PVPEnabled", "bool", False, "PvP Enabled", "Combat", "Enables player-versus-player combat."),
    ConanSettingDefinition("CanDamagePlayerOwnedStructures", SERVER_SETTINGS_INI, "ServerSettings", "CanDamagePlayerOwnedStructures", "bool", False, "Building Damage", "Combat", "Allows player-owned structures to take damage."),
    ConanSettingDefinition("DropEquipmentOnDeath", SERVER_SETTINGS_INI, "ServerSettings", "DropEquipmentOnDeath", "bool", True, "Drop Equipment on Death", "Survival", "Controls whether equipment is dropped on player death."),
    ConanSettingDefinition("EverybodyCanLootCorpse", SERVER_SETTINGS_INI, "ServerSettings", "EverybodyCanLootCorpse", "bool", False, "Everyone Can Loot Corpses", "Survival", "Allows other players to loot player corpses."),
    ConanSettingDefinition("OfflinePlayersRemainInTheWorld", SERVER_SETTINGS_INI, "ServerSettings", "OfflinePlayersRemainInTheWorld", "bool", True, "Offline Bodies Remain", "Survival", "Keeps disconnected player characters in the world."),
    ConanSettingDefinition("PlayerDamageMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerDamageMultiplier", "float", 1.0, "Player Damage", "Combat", "Multiplier for damage dealt by players.", minimum=0, maximum=20, step=0.1),
    ConanSettingDefinition("PlayerDamageTakenMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerDamageTakenMultiplier", "float", 1.0, "Player Damage Taken", "Combat", "Multiplier for damage received by players.", minimum=0, maximum=20, step=0.1),
    ConanSettingDefinition("NPCDamageMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "NPCDamageMultiplier", "float", 1.0, "NPC Damage", "Combat", "Multiplier for damage dealt by NPCs.", minimum=0, maximum=20, step=0.1),
    ConanSettingDefinition("NPCDamageTakenMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "NPCDamageTakenMultiplier", "float", 1.0, "NPC Damage Taken", "Combat", "Multiplier for damage received by NPCs.", minimum=0, maximum=20, step=0.1),
    ConanSettingDefinition("PlayerXPRateMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerXPRateMultiplier", "float", 1.0, "Player XP Rate", "Progression", "Global player experience multiplier.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerXPKillMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerXPKillMultiplier", "float", 1.0, "Kill XP", "Progression", "Experience multiplier for kills.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerXPHarvestMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerXPHarvestMultiplier", "float", 1.0, "Harvest XP", "Progression", "Experience multiplier for harvesting.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerXPCraftMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerXPCraftMultiplier", "float", 1.0, "Craft XP", "Progression", "Experience multiplier for crafting.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerXPPassiveMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerXPPassiveMultiplier", "float", 1.0, "Passive XP", "Progression", "Passive experience multiplier.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("HarvestAmountMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "HarvestAmountMultiplier", "float", 1.0, "Harvest Amount", "Harvesting & Crafting", "Multiplier for harvested resources.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("ResourceRespawnSpeedMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "ResourceRespawnSpeedMultiplier", "float", 1.0, "Resource Respawn Speed", "Harvesting & Crafting", "Multiplier controlling resource respawn speed.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("CraftingCostMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "CraftingCostMultiplier", "float", 1.0, "Crafting Cost", "Harvesting & Crafting", "Multiplier for crafting material costs.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("ItemConvertionMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "ItemConvertionMultiplier", "float", 1.0, "Crafting Time", "Harvesting & Crafting", "Multiplier used by Conan for item conversion/crafting time.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("ThrallConversionMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "ThrallConversionMultiplier", "float", 1.0, "Thrall Conversion Time", "Thralls", "Multiplier for thrall conversion time.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("FuelBurnTimeMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "FuelBurnTimeMultiplier", "float", 1.0, "Fuel Burn Time", "Harvesting & Crafting", "Multiplier for fuel burn duration.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("DurabilityMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "DurabilityMultiplier", "float", 1.0, "Durability", "Survival", "Multiplier controlling item durability loss.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerActiveHungerMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerActiveHungerMultiplier", "float", 1.0, "Active Hunger", "Survival", "Hunger rate while active.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerActiveThirstMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerActiveThirstMultiplier", "float", 1.0, "Active Thirst", "Survival", "Thirst rate while active.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerStaminaCostMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "PlayerStaminaCostMultiplier", "float", 1.0, "Stamina Cost", "Survival", "Multiplier for player stamina costs.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("PlayerStaminaRegenSpeedScale", SERVER_SETTINGS_INI, "ServerSettings", "PlayerStaminaRegenSpeedScale", "float", 1.0, "Stamina Regeneration", "Survival", "Multiplier for player stamina regeneration.", minimum=0, maximum=100, step=0.1),
    ConanSettingDefinition("DayCycleSpeedScale", SERVER_SETTINGS_INI, "ServerSettings", "DayCycleSpeedScale", "float", 1.0, "Day Cycle Speed", "Day & Night", "Overall day/night cycle speed multiplier.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("DayTimeSpeedScale", SERVER_SETTINGS_INI, "ServerSettings", "DayTimeSpeedScale", "float", 1.0, "Day Time Speed", "Day & Night", "Daytime speed multiplier.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("NightTimeSpeedScale", SERVER_SETTINGS_INI, "ServerSettings", "NightTimeSpeedScale", "float", 1.0, "Night Time Speed", "Day & Night", "Nighttime speed multiplier.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("DawnDuskSpeedScale", SERVER_SETTINGS_INI, "ServerSettings", "DawnDuskSpeedScale", "float", 1.0, "Dawn/Dusk Speed", "Day & Night", "Dawn and dusk transition speed multiplier.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("NPCRespawnMultiplier", SERVER_SETTINGS_INI, "ServerSettings", "NPCRespawnMultiplier", "float", 1.0, "NPC Respawn Multiplier", "World", "Multiplier controlling NPC respawn timing.", minimum=0.01, maximum=100, step=0.1),
    ConanSettingDefinition("ServerTransferEnabled", SERVER_SETTINGS_INI, "ServerSettings", "ServerTransferEnabled", "bool", True, "Character Transfers", "Gameplay", "Allows compatible character transfers onto this server.", popular=False),
    ConanSettingDefinition("CanImportDirectlyFromSameServer", SERVER_SETTINGS_INI, "ServerSettings", "CanImportDirectlyFromSameServer", "bool", True, "Same-Server Character Reimport", "Gameplay", "Allows a stored character originating here to be reimported.", popular=False),
)

BY_KEY = {definition.key: definition for definition in DEFINITIONS}
_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def config_dir(server_path: Path) -> Path:
    return server_path / WINDOWS_SERVER_RELATIVE


def config_path(server_path: Path, file_name: str) -> Path:
    return config_dir(server_path) / file_name


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.is_file() else ""


def _find_value(text: str, section: str, key: str) -> str | None:
    current_section = None
    key_re = re.compile(rf"^(\s*){re.escape(key)}\s*=(.*)$", re.IGNORECASE)
    for line in text.splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1)
            continue
        if current_section == section:
            key_match = key_re.match(line)
            if key_match:
                return key_match.group(2).strip()
    return None


def _set_value(text: str, section: str, key: str, value: str) -> str:
    lines = text.splitlines()
    section_index = None
    section_end = len(lines)
    current_section = None
    key_re = re.compile(rf"^(\s*){re.escape(key)}\s*=(.*)$", re.IGNORECASE)

    for index, line in enumerate(lines):
        section_match = _SECTION_RE.match(line)
        if section_match:
            if current_section == section and section_end == len(lines):
                section_end = index
            current_section = section_match.group(1)
            if current_section == section and section_index is None:
                section_index = index
            continue
        if current_section == section:
            key_match = key_re.match(line)
            if key_match:
                lines[index] = f"{key_match.group(1)}{key}={value}"
                return "\n".join(lines).rstrip() + "\n"

    if section_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"[{section}]", f"{key}={value}"])
    else:
        lines.insert(section_end, f"{key}={value}")

    return "\n".join(lines).rstrip() + "\n"


def _encode(value: Any, field_type: str) -> str:
    if field_type == "bool":
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return "True"
            if normalized in {"false", "0", "no", "off"}:
                return "False"
            raise ValueError(f"Invalid boolean value: {value!r}")
        return "True" if bool(value) else "False"
    if field_type == "int":
        if isinstance(value, bool):
            raise ValueError("Boolean is not a valid integer.")
        return str(int(value))
    if field_type == "float":
        if isinstance(value, bool):
            raise ValueError("Boolean is not a valid decimal value.")
        normalized = str(value).strip().replace(",", ".")
        parsed = float(normalized)
        return format(parsed, ".12g")
    if field_type == "string":
        return str(value).replace("\r", "").replace("\n", "")
    return str(value)


def _decode(raw: str | None, definition: ConanSettingDefinition) -> Any:
    if raw is None:
        return definition.default
    if definition.field_type == "bool":
        return raw.strip().lower() in {"true", "1", "yes", "on"}
    if definition.field_type == "int":
        try:
            return int(raw.strip())
        except ValueError:
            return definition.default
    if definition.field_type == "float":
        try:
            return float(raw.strip().replace(",", "."))
        except ValueError:
            return definition.default
    return raw


def _validate(definition: ConanSettingDefinition, value: Any) -> Any:
    if definition.field_type == "int":
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{definition.label} must be an integer.") from exc
        if definition.minimum is not None and parsed < definition.minimum:
            raise ValueError(f"{definition.label} must be at least {definition.minimum}.")
        if definition.maximum is not None and parsed > definition.maximum:
            raise ValueError(f"{definition.label} must be at most {definition.maximum}.")
        return parsed
    if definition.field_type == "float":
        try:
            parsed = float(str(value).strip().replace(",", "."))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{definition.label} must be a decimal number.") from exc
        if definition.minimum is not None and parsed < definition.minimum:
            raise ValueError(f"{definition.label} must be at least {definition.minimum}.")
        if definition.maximum is not None and parsed > definition.maximum:
            raise ValueError(f"{definition.label} must be at most {definition.maximum}.")
        return parsed
    if definition.field_type == "bool":
        _encode(value, "bool")
        return value
    text = str(value).replace("\r", "").replace("\n", "")
    if "[" in text or "]" in text:
        raise ValueError(f"{definition.label} contains invalid INI control characters.")
    return text


def _section_entries(text: str, section: str) -> list[tuple[str, str]]:
    current_section = None
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group(1)
            continue
        if current_section != section or "=" not in line or line.lstrip().startswith((";", "#")):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            entries.append((key, value.strip()))
    return entries


_DYNAMIC_HELP: dict[str, str] = {
    "PlayerStaminaCostSprintMultiplier": "Controls stamina consumed specifically while sprinting. 1 is the normal cost; lower values reduce sprint stamina use and higher values increase it.",
    "PlayerMovementSpeedScale": "Controls player movement speed. 1 is normal movement speed; lower values slow players and higher values make them move faster.",
    "PlayerSprintSpeedScale": "Controls player sprint speed. 1 is normal sprint speed; lower values slow sprinting and higher values increase it.",
    "PlayerHealthRegenSpeedScale": "Controls player health regeneration speed. 1 is normal regeneration; lower values regenerate more slowly and higher values regenerate faster.",
    "PlayerEncumbranceMultiplier": "Controls how strongly carried weight contributes to encumbrance. 1 is the normal value.",
    "PlayerEncumbrancePenaltyMultiplier": "Controls the movement/stamina penalty caused by encumbrance. 1 is the normal penalty strength.",
    "PlayerKnockbackMultiplier": "Controls knockback applied to players. 1 is normal knockback; lower values reduce it and higher values increase it.",
    "NPCKnockbackMultiplier": "Controls knockback applied to NPCs. 1 is normal knockback; lower values reduce it and higher values increase it.",
    "StructureDamageMultiplier": "Controls damage dealt to structures. 1 is normal structure damage; lower values reduce it and higher values increase it.",
    "StructureHealthMultiplier": "Controls structure health. 1 is normal structure health; lower values reduce durability and higher values increase it.",
    "NPCHealthMultiplier": "Controls NPC health. 1 is normal health; lower values reduce NPC health and higher values increase it.",
    "MinionDamageMultiplier": "Controls damage dealt by follower/minion actors. 1 is normal damage.",
    "MinionDamageTakenMultiplier": "Controls damage received by follower/minion actors. 1 is normal incoming damage.",
    "PlayerXPTimeMultiplier": "Controls experience gained over time. 1 is the normal rate; higher values award more passive/time-based XP.",
    "FriendlyFireDamageMultiplier": "Controls friendly-fire damage. 1 is full normal damage; lower values reduce friendly-fire damage.",
    "NPCMaxSpawnCapMultiplier": "Controls the maximum NPC population cap. 1 is the normal cap; higher values permit more NPCs.",
    "CraftFromStorageRadius": "Radius in centimeters within which crafting stations can pull materials from nearby storage.",
    "BuildFromStorageRadius": "Radius in centimeters within which building can consume materials from nearby storage.",
    "PVPBuildFromStorageRadius": "Storage-use radius in centimeters for building while PvP rules are active.",
    "PersonalCraftFromStorageRadius": "Radius in centimeters for player-personal crafting to pull materials from nearby storage.",
    "BuildingReplicationDistance": "Controls how far building actors are replicated to clients. Higher values can increase network/server load.",
    "CombatModeModifier": "Selects the server combat ruleset. Conan Enhanced documents value 1 as PvE-Conflict (PvE-C).",
    "ContainersIgnoreOwnership": "When enabled, container access ignores normal ownership restrictions.",
    "LandClaimRadiusMultiplier": "Controls land-claim radius around buildings. It also affects nearby resource/NPC respawn and how close other players may build. 1 is normal.",
    "BuildingPreloadRadius": "Controls the radius used to preload nearby building data for players.",
    "DynamicBuildingDamage": "Enables dynamic building-damage handling used by the configured dynamic damage period.",
    "DynamicBuildingDamagePeriod": "Controls the period used by dynamic building damage, in seconds.",
    "CreativeModeServer": "Controls server-wide creative mode. Use the value supported by the current Conan Enhanced server build.",
    "ServerMessageOfTheDay": "Message displayed to players as the server message of the day.",
    "KickAFKPercentage": "Controls the server-load/player-percentage threshold used by Conan's AFK kick logic.",
    "KickAFKTime": "Controls how long a player may remain AFK before being eligible for removal, in seconds.",
    "OfflinePlayersUnconsciousBodiesHours": "Controls how many hours offline player bodies remain unconscious in the world.",
    "ShowOnlinePlayers": "Controls how much online-player information the server exposes.",
    "CorpsesPerPlayer": "Maximum number of retained corpses per player.",
    "PlayerCorpseLifeTime": "Controls player-corpse lifetime in seconds.",
    "NPCCorpseLifeTime": "Controls NPC-corpse lifetime in seconds.",
    "StaminaRegenerationTime": "Controls the base time used for stamina regeneration.",
    "StaminaExhaustionTime": "Controls the exhaustion recovery time used after stamina is fully depleted.",
    "StaminaStaticRegenRateMultiplier": "Controls stamina regeneration while stationary. 1 is the normal rate.",
    "StaminaMovingRegenRateMultiplier": "Controls stamina regeneration while moving. 1 is the normal rate.",
    "StaminaOnConsumeRegenPause": "Controls the regeneration pause after stamina is consumed.",
    "StaminaOnExhaustionRegenPause": "Controls the regeneration pause after complete stamina exhaustion.",
    "ThrallScoutingTimeMinutes": "Controls how many minutes a follower can remain in scouting state before returning home.",
    "ThrallMinDistanceAwayFromHome": "Controls the minimum distance a follower must be from home for relevant return/scouting behavior.",
    "ThrallTeleportingCooldown": "Controls the cooldown for follower teleport/return behavior.",
    "MinionPopulationBaseValue": "Base server-wide thrall and pet population allowance when population limits are enabled.",
    "MinionPopulationPerPlayer": "Additional thrall and pet population allowance granted per player when population limits are enabled.",
    "MinionOverpopulationCleanup": "Controls the interval used to clean up population above the configured follower limit.",
    "MinionOverpopulationAllowed": "Controls how far follower population may exceed the configured limit before cleanup applies.",
    "EnableFollowerDbno": "Enables Down-But-Not-Out behavior for thralls and pets instead of immediate death where supported.",
    "UseMinionPopulationLimit": "Enables the server population limit for thralls and pets.",
    "FollowerRescueCooldown": "Cooldown before follower rescue can be used again.",
    "DamageCooldownBeforeRescue": "Minimum time after taking damage before follower rescue is allowed.",
    "ThrallCorruptionRemovalMultiplier": "Controls how effectively thralls remove corruption. 1 is normal effectiveness.",
    "PlayerCorruptionGainMultiplier": "Controls general player corruption gain. 1 is the normal rate.",
    "PlayerCorruptionGainFromSorceryMultiplier": "Controls corruption gained specifically from sorcery. 1 is the normal rate.",
    "AnimalPenCraftingTimeMultiplier": "Controls animal-pen crafting/conversion time. 1 is normal; lower values are faster.",
    "FeedBoxRangeMultiplier": "Controls the effective range of follower food containers. 1 is the normal range.",
    "BuildingDamageMultiplier": "Controls damage received by buildings. 1 is normal building damage.",
    "UnconsciousTimeSeconds": "Time in seconds that an unconscious thrall remains unconscious before waking.",
    "ConciousnessDamageMultiplier": "Controls concussion/knockout damage used to render NPCs unconscious. 1 is normal.",
    "ThrallDamageToPlayersMultiplier": "Controls damage dealt by thralls to players. 1 is normal damage.",
    "ThrallDamageToNPCsMultiplier": "Controls damage dealt by thralls to NPCs. 1 is normal damage.",
    "DisableBuildingAbandonment": "Disables the building abandonment/decay system when enabled.",
    "MaxBuildingDecayTime": "Maximum building decay time used by the decay system.",
    "MaxDecayTimeToAutoDemolish": "Maximum decay time before eligible structures can be automatically demolished.",
    "ThrallDecayTime": "Controls thrall decay time. This setting matters when thrall decay is enabled.",
    "DisableThrallDecay": "Disables thrall decay when enabled.",
    "BuildingDecayTimeMultiplier": "Controls building decay duration. 1 is the normal decay rate/duration basis.",
    "EnableTargetLock": "Enables target-lock functionality for players.",
    "EnableFatalities": "Enables the fatalities system.",
    "EnableClanMarkers": "Enables clan/guild map markers.",
    "bUndermeshDetectionEnabled": "Enables server-side undermesh detection.",
    "AllowedTimeUndermesh": "Controls how long a player may remain detected under the mesh before the configured protection reacts.",
    "serverVoiceChat": "Controls server voice-chat behavior.",
    "AvatarsDisabled": "Disables avatar summoning when enabled.",
    "AvatarLifetime": "Controls avatar lifetime after summoning, in seconds.",
    "AvatarSummonTime": "Controls the time required to summon an avatar, in seconds.",
    "MaxDeathMapMarkers": "Maximum number of death markers retained on the map.",
    "IsBattlEyeEnabled": "Enables or disables BattlEye anti-cheat for the server.",
    "MaxAllowedPing": "Maximum allowed player ping. A value of 0 normally disables the ping limit.",
    "AllowFamilySharedAccount": "Allows Steam Family Shared accounts to join when enabled.",
    "BuildingPickupEnabled": "Allows placed building pieces to be picked back up when enabled.",
    "PoiProtectionEnabled": "Enables protection rules around points of interest.",
    "EventSystemEnabled": "Enables Conan's server event system.",
    "StabilityLossMultiplier": "Controls building stability loss. 1 is normal stability loss.",
    "BuildingValidationEnabled": "Enables additional building placement/validation checks.",
    "AllowBuildingAnywhere": "Allows building in normally restricted point-of-interest areas when enabled.",
    "HealthbarVisibilityDistance": "Maximum distance at which health bars are visible.",
    "DisableChatFormatting": "Disables player chat formatting when enabled.",
    "EnableLoginQueue": "Enables the login queue when the server is full or busy.",
    "DisconnectionGraceTime": "Grace period after a disconnect before the server fully treats the player as disconnected.",
}


def _dynamic_help_for(key: str, label: str, field_type: str) -> str:
    explicit = _DYNAMIC_HELP.get(key)
    if explicit:
        return explicit
    normalized = label.lower()
    if field_type == "bool":
        return f"Enables or disables {normalized}."
    if key.endswith("Multiplier") or "Multiplier" in key:
        return f"Controls {normalized}. A value of 1 is the normal baseline; lower values reduce the effect and higher values increase it."
    if key.endswith("Seconds") or key.endswith("Time") or "Cooldown" in key:
        return f"Controls {normalized}. The value is a time/cooldown used by Conan Exiles Enhanced; keep the unit shown by the setting name."
    if key.endswith("Radius") or "Distance" in key or "Range" in key:
        return f"Controls {normalized}, generally as an in-world distance/radius value. Higher values increase the affected range."
    if key.endswith("Start") or key.endswith("End"):
        return f"Controls the configured schedule boundary for {normalized}. It is used together with the matching time-restriction setting."
    if "Password" in key:
        return f"Configures {normalized}. EGM treats this value as sensitive and does not include it in activity-log details."
    return f"Controls the Conan Exiles Enhanced ServerSettings.ini option '{key}'. The current value is loaded directly from this server and is preserved when saved."


def _dynamic_numeric_type(key: str, raw: str) -> tuple[str, Any] | None:
    normalized = raw.strip().replace(",", ".")
    float_semantic = any(token in key for token in ("Multiplier", "Scale"))
    try:
        if float_semantic:
            return "float", float(normalized)
        return "int", int(normalized)
    except ValueError:
        try:
            return "float", float(normalized)
        except ValueError:
            return None


def _infer_dynamic_field(key: str, raw: str) -> dict[str, Any]:
    lowered = raw.strip().lower()
    sensitive = any(token in key.casefold() for token in ("password", "secret", "token", "apikey", "api_key"))
    if lowered in {"true", "false"}:
        field_type = "bool"
        value: Any = lowered == "true"
    else:
        numeric = _dynamic_numeric_type(key, raw)
        if numeric is not None:
            field_type, value = numeric
        else:
            value = raw
            field_type = "string"
    label = re.sub(r"(?<!^)(?=[A-Z])", " ", key).replace("_", " ").strip() or key
    help_text = _dynamic_help_for(key, label, field_type)
    return {
        "key": key, "type": field_type, "value": value, "label": label,
        "description": "Loaded directly from this server's ServerSettings.ini.",
        "help": help_text,
        "group": "Additional ServerSettings", "options": None, "sensitive": sensitive,
        "popular": False, "minimum": None, "maximum": None, "step": None,
        "restartRequired": True, "sourceFile": SERVER_SETTINGS_INI,
        "sourceSection": "ServerSettings", "sourceKey": key, "dynamic": True,
    }


def _dynamic_existing_keys(server_path: Path) -> set[str]:
    text = _read_text(config_path(server_path, SERVER_SETTINGS_INI))
    return {key for key, _ in _section_entries(text, "ServerSettings")} - set(BY_KEY)


def read_all_settings(server_path: Path) -> list[dict[str, Any]]:
    cache: dict[str, str] = {}
    fields = []
    for definition in DEFINITIONS:
        text = cache.setdefault(definition.file_name, _read_text(config_path(server_path, definition.file_name)))
        raw = _find_value(text, definition.section, definition.ini_key)
        fields.append(definition.public_field(_decode(raw, definition)))
    server_settings_text = cache.setdefault(SERVER_SETTINGS_INI, _read_text(config_path(server_path, SERVER_SETTINGS_INI)))
    for key, raw in _section_entries(server_settings_text, "ServerSettings"):
        if key not in BY_KEY:
            fields.append(_infer_dynamic_field(key, raw))
    return fields


def write_settings(server_path: Path, updates: dict[str, Any]) -> list[str]:
    dynamic_keys = _dynamic_existing_keys(server_path)
    unknown = sorted(set(updates) - set(BY_KEY) - dynamic_keys)
    if unknown:
        raise ValueError(f"Unknown Conan setting(s): {', '.join(unknown)}")

    pending: dict[str, list[tuple[str, str, str]]] = {}
    changed: list[str] = []
    for key, value in updates.items():
        definition = BY_KEY.get(key)
        if definition is not None:
            validated = _validate(definition, value)
            encoded = _encode(validated, definition.field_type)
            file_name, section, ini_key = definition.file_name, definition.section, definition.ini_key
        else:
            raw = str(value).replace("\r", "").replace("\n", "")
            if "[" in raw or "]" in raw:
                raise ValueError(f"{key} contains invalid INI control characters.")
            existing_text = _read_text(config_path(server_path, SERVER_SETTINGS_INI))
            existing_raw = _find_value(existing_text, "ServerSettings", key)
            inferred = _infer_dynamic_field(key, existing_raw or "")
            if inferred["type"] == "float":
                try:
                    encoded = format(float(raw.replace(",", ".")), ".15g")
                except ValueError as exc:
                    raise ValueError(f"{key} must be a decimal number.") from exc
            elif inferred["type"] == "int":
                try:
                    encoded = str(int(raw))
                except ValueError as exc:
                    raise ValueError(f"{key} must be a whole number.") from exc
            else:
                encoded = raw
            file_name, section, ini_key = SERVER_SETTINGS_INI, "ServerSettings", key
        path = config_path(server_path, file_name)
        current = _find_value(_read_text(path), section, ini_key)
        if current != encoded:
            changed.append(key)
            pending.setdefault(file_name, []).append((section, ini_key, encoded))

    config_dir(server_path).mkdir(parents=True, exist_ok=True)
    for file_name, items in pending.items():
        path = config_path(server_path, file_name)
        text = _read_text(path)
        for section, ini_key, encoded in items:
            text = _set_value(text, section, ini_key, encoded)
        temporary = path.with_suffix(path.suffix + ".egm-tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    return changed


def read_max_players(server_path: Path) -> int:
    definition = BY_KEY["MaxPlayers"]
    text = _read_text(config_path(server_path, definition.file_name))
    return int(_decode(_find_value(text, definition.section, definition.ini_key), definition))


def _new_secret() -> str:
    return secrets.token_urlsafe(24)


def initialize_settings(
    server_path: Path,
    *,
    server_name: str,
    ports: dict[str, int],
    max_players: int,
    rcon_password: str | None = None,
    admin_password: str | None = None,
    server_password: str = "",
) -> dict[str, Path]:
    updates = {
        "ServerName": server_name,
        "ServerPassword": server_password,
        "GamePort": int(ports["game"]),
        "QueryPort": int(ports["query"]),
        "MaxPlayers": int(max_players),
        "RconEnabled": True,
        "RconPort": int(ports["rcon"]),
        "RconPassword": rcon_password or _new_secret(),
        "AdminPassword": admin_password or _new_secret(),
        "NetServerMaxTickRate": 30,
        "ServerTransferEnabled": True,
        "CanImportDirectlyFromSameServer": True,
    }
    write_settings(server_path, updates)
    return {
        ENGINE_INI: config_path(server_path, ENGINE_INI),
        GAME_INI: config_path(server_path, GAME_INI),
        SERVER_SETTINGS_INI: config_path(server_path, SERVER_SETTINGS_INI),
    }

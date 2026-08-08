import type { GameCapabilities, ServerStatus } from "@/types/models";

export type GameCapability = keyof GameCapabilities;

const STABLE_FALLBACK: GameCapabilities = {
  server_control: true,
  server_settings: true,
  steam_workshop: true,
  nexus_mods: true,
  live_console: false,
  rcon: false,
  rest_api: true,
  ue4ss: true,
  firewall_management: true,
  backups: true,
  performance_monitoring: true,
};

export function capabilitiesFor(
  status: ServerStatus | null | undefined,
): GameCapabilities {
  return status?.capabilities ?? STABLE_FALLBACK;
}

export function supportsCapability(
  status: ServerStatus | null | undefined,
  capability: GameCapability,
): boolean {
  return capabilitiesFor(status)[capability];
}

export function supportsAnyCapability(
  status: ServerStatus | null | undefined,
  capabilities: readonly GameCapability[],
): boolean {
  const resolved = capabilitiesFor(status);
  return capabilities.some((capability) => resolved[capability]);
}

import type { GameCatalog, GameDefinition } from "@/types/models";

const sharedConanCapabilities = {
  server_control: true,
  server_settings: true,
  steam_workshop: true,
  nexus_mods: false,
  live_console: true,
  rcon: true,
  rest_api: false,
  ue4ss: false,
  firewall_management: true,
  backups: false,
  performance_monitoring: true,
};

export const FALLBACK_GAMES: GameDefinition[] = [
  {
    id: "palworld", family: "palworld", edition: "standard", label: "Palworld", shortLabel: "Palworld",
    availability: "available", deployable: true, steamServerAppId: 2394010, steamWorkshopAppId: 1623730, steamBranch: null,
    executableNames: ["PalServer.exe"], defaultPorts: { game: 8211, restApi: 8212, query: 8213 },
    portDefinitions: [
      { key: "game", label: "Game Port", default: 8211, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "restApi", label: "REST API Port", default: 8212, protocol: "TCP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "query", label: "Steam Query Port", default: 8213, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
    ],
    capabilities: { server_control: true, server_settings: true, steam_workshop: true, nexus_mods: true, live_console: false, rcon: false, rest_api: true, ue4ss: true, firewall_management: true, backups: true, performance_monitoring: true },
  },
  {
    id: "conan_exiles_enhanced", family: "conan_exiles", edition: "enhanced", label: "Conan Exiles Enhanced", shortLabel: "Conan Enhanced",
    availability: "available", deployable: true, steamServerAppId: 443030, steamWorkshopAppId: 440900, steamBranch: null,
    executableNames: ["ConanSandbox/Binaries/Win64/ConanSandboxServer-Win64-Shipping.exe"],
    defaultPorts: { game: 7777, pinger: 7778, query: 27015, rcon: 25575 },
    portDefinitions: [
      { key: "game", label: "Game Port", default: 7777, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "pinger", label: "Pinger Port", default: 7778, protocol: "UDP", configurable: false, relative_to: "game", offset: 1, firewall: true },
      { key: "query", label: "Server Query Port", default: 27015, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "rcon", label: "RCON Port", default: 25575, protocol: "TCP", configurable: true, relative_to: null, offset: 0, firewall: true },
    ], capabilities: sharedConanCapabilities,
  },
  {
    id: "conan_exiles_legacy", family: "conan_exiles", edition: "legacy", label: "Conan Exiles Legacy", shortLabel: "Conan Legacy",
    availability: "available", deployable: true, steamServerAppId: 443030, steamWorkshopAppId: 440900, steamBranch: "conan-exiles-legacy",
    executableNames: ["ConanSandbox/Binaries/Win64/ConanSandboxServer-Win64-Shipping.exe"],
    defaultPorts: { game: 7777, pinger: 7778, query: 27015, rcon: 25575 },
    portDefinitions: [
      { key: "game", label: "Game Port", default: 7777, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "pinger", label: "Pinger Port", default: 7778, protocol: "UDP", configurable: false, relative_to: "game", offset: 1, firewall: true },
      { key: "query", label: "Server Query Port", default: 27015, protocol: "UDP", configurable: true, relative_to: null, offset: 0, firewall: true },
      { key: "rcon", label: "RCON Port", default: 25575, protocol: "TCP", configurable: true, relative_to: null, offset: 0, firewall: true },
    ], capabilities: sharedConanCapabilities,
  },
];

export const FALLBACK_GAME_CATALOG: GameCatalog = { defaultGameId: "palworld", games: FALLBACK_GAMES };

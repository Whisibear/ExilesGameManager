import { api } from "./httpClient";
import type { SettingField } from "@/types/models";

export interface ServerSettingsView {
  fields: SettingField[];
  gameId: string;
  gameFamily: string;
  gameEdition: string;
  gameLabel: string;
  providerId: string;
  restartRequired: boolean;
  changedKeys: string[];
}

export async function getSettings(): Promise<ServerSettingsView> {
  return api.get<ServerSettingsView>("/api/server-settings");
}

export async function updateSettings(values: Record<string, unknown>): Promise<ServerSettingsView> {
  return api.post<ServerSettingsView>("/api/server-settings", { values });
}

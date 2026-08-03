import { api } from "./httpClient";
import type { SteamWorkshopList, SteamWorkshopPage } from "@/types/models";

export async function getModList(list: SteamWorkshopList, offset = 0): Promise<SteamWorkshopPage> {
  return api.get<SteamWorkshopPage>(`/api/integrations/steam-workshop/mods?list=${list}&offset=${offset}`);
}

export async function searchMods(query: string, offset = 0): Promise<SteamWorkshopPage> {
  return api.get<SteamWorkshopPage>(`/api/integrations/steam-workshop/search?q=${encodeURIComponent(query)}&offset=${offset}`);
}

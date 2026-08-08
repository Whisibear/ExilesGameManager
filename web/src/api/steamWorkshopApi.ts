import { api } from "./httpClient";
import type { SteamWorkshopList, SteamWorkshopPage } from "@/types/models";

export type SteamWorkshopCatalog = "palworld" | "conan";

export async function getModList(list: SteamWorkshopList, offset = 0, catalog?: SteamWorkshopCatalog): Promise<SteamWorkshopPage> {
  const catalogQuery = catalog ? `&catalog=${catalog}` : "";
  return api.get<SteamWorkshopPage>(`/api/integrations/steam-workshop/mods?list=${list}&offset=${offset}${catalogQuery}`);
}

export async function searchMods(query: string, offset = 0, catalog?: SteamWorkshopCatalog): Promise<SteamWorkshopPage> {
  const catalogQuery = catalog ? `&catalog=${catalog}` : "";
  return api.get<SteamWorkshopPage>(`/api/integrations/steam-workshop/search?q=${encodeURIComponent(query)}&offset=${offset}${catalogQuery}`);
}

import { api } from "./httpClient";
import type { NexusAccount, NexusModList, NexusModPage, NexusOAuthStart, NexusOAuthStatus } from "@/types/models";

// GET /api/integrations/nexus/account
export async function getAccount(): Promise<NexusAccount> {
  return api.get<NexusAccount>("/api/integrations/nexus/account");
}

// POST /api/integrations/nexus/oauth/start
export async function startOAuth(): Promise<NexusOAuthStart> {
  return api.post<NexusOAuthStart>("/api/integrations/nexus/oauth/start");
}

// GET /api/integrations/nexus/oauth/status/{requestId}
export async function getOAuthStatus(requestId: string): Promise<NexusOAuthStatus> {
  return api.get<NexusOAuthStatus>(`/api/integrations/nexus/oauth/status/${requestId}`);
}

// POST /api/integrations/nexus/disconnect
export async function disconnectAccount(): Promise<NexusAccount> {
  return api.post<NexusAccount>("/api/integrations/nexus/disconnect");
}

// Paginated (TICKET-0149) - pass the previous page's result count as offset
// to fetch the next page, using totalCount to know when to stop.
export async function getModList(list: NexusModList, offset = 0): Promise<NexusModPage> {
  return api.get<NexusModPage>(`/api/integrations/nexus/mods?list=${list}&offset=${offset}`);
}

// GET /api/integrations/nexus/search?q=... - real Nexus-side search by name,
// not just a client-side filter over an already-loaded list (TICKET-0144),
// paginated (TICKET-0149) the same way as getModList.
export async function searchMods(query: string, offset = 0): Promise<NexusModPage> {
  return api.get<NexusModPage>(`/api/integrations/nexus/search?q=${encodeURIComponent(query)}&offset=${offset}`);
}

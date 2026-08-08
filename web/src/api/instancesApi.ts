import { api } from "./httpClient";
import type {
  DeployJob,
  GameCatalog,
  GamePortDefinition,
  InstanceListView,
  ServerInstance,
} from "@/types/models";

export async function listGames(): Promise<GameCatalog> { return api.get<GameCatalog>("/api/instances/games"); }

// GET /api/instances
export async function list(): Promise<InstanceListView> {
  return api.get<InstanceListView>("/api/instances");
}

// GET /api/instances/active
export async function getActive(): Promise<ServerInstance | null> {
  return api.get<ServerInstance | null>("/api/instances/active");
}

// POST /api/instances/active
export async function setActive(id: string): Promise<InstanceListView> {
  return api.post<InstanceListView>("/api/instances/active", { id });
}

// DELETE /api/instances/{id}
export async function removeInstance(id: string, deleteFiles = false): Promise<InstanceListView> {
  const suffix = deleteFiles ? "?deleteFiles=true" : "";
  return api.delete<InstanceListView>(`/api/instances/${id}${suffix}`);
}

// POST /api/instances/{id}/open
export async function openInstanceFolder(id: string): Promise<{ opened: boolean }> {
  return api.post<{ opened: boolean }>(`/api/instances/${id}/open`);
}

// POST /api/instances/{id}/community-server
export async function setCommunityServer(id: string, enabled: boolean): Promise<InstanceListView> {
  return api.post<InstanceListView>(`/api/instances/${id}/community-server`, { enabled });
}

// POST /api/instances/{id}/query-port
export async function setQueryPort(id: string, port: number): Promise<InstanceListView> {
  return api.post<InstanceListView>(`/api/instances/${id}/query-port`, { port });
}

export interface LaunchOptionsParams {
  usePerfThreads: boolean;
  noAsyncLoadingThread: boolean;
  useMultithreadForDs: boolean;
  publicLobby: boolean;
  usePublicIpOverride: boolean;
  publicIpOverride: string;
  usePublicPortOverride: boolean;
  useQueryPort: boolean;
}

// POST /api/instances/{id}/launch-options
export async function setLaunchOptions(id: string, params: LaunchOptionsParams): Promise<InstanceListView> {
  return api.post<InstanceListView>(`/api/instances/${id}/launch-options`, params);
}

export interface ImportAnalysisIssue {
  code: string;
  severity: "info" | "warning" | "error";
  titleKey: string;
  messageKey: string;
  fallbackTitle: string;
  fallbackMessage: string;
}

export interface ImportAnalysis {
  gameId: string;
  gameFamily: string;
  serverPath: string;
  ready: boolean;
  checks: Record<string, boolean>;
  issues: ImportAnalysisIssue[];
}

export interface ImportExistingResult extends InstanceListView {
  importAnalysis?: ImportAnalysis;
}

// POST /api/instances/import
export async function importExisting(name: string, path: string, gameId = "palworld"): Promise<ImportExistingResult> {
  return api.post<ImportExistingResult>("/api/instances/import", { name, path, gameId });
}

// POST /api/instances/import/detect
export interface ImportDetectionResult extends Partial<InstanceListView> {
  detected: boolean;
  path?: string | null;
  message?: string;
}

export async function importDetected(): Promise<ImportDetectionResult> {
  return api.post<ImportDetectionResult>("/api/instances/import/detect");
}

// POST /api/instances/import/browse
export async function browseImportDir(): Promise<{ path: string | null }> {
  return api.post<{ path: string | null }>("/api/instances/import/browse");
}

// POST /api/instances/deploy/browse
export async function browseDeployParentDir(): Promise<{ path: string | null }> {
  return api.post<{ path: string | null }>("/api/instances/deploy/browse");
}

// GET /api/instances/deploy/default-location
export async function getDefaultDeployLocation(): Promise<{ path: string }> {
  return api.get<{ path: string }>("/api/instances/deploy/default-location");
}

export interface PortSuggestion extends GamePortDefinition {
  port: number;
}

export async function suggestDeployPorts(
  gameId: string,
): Promise<{ gameId: string; ports: PortSuggestion[] }> {
  return api.get<{ gameId: string; ports: PortSuggestion[] }>(
    `/api/instances/deploy/ports?gameId=${encodeURIComponent(gameId)}`,
  );
}

export interface DeployParams {
  name: string;
  gameId?: string;
  gamePort: number;
  rconPort: number;
  queryPort: number;
  maxPlayers: number;
  installParentDir?: string | null;
  templateInstanceId?: string | null;
}

// POST /api/instances/deploy
export async function deploy(params: DeployParams): Promise<{ jobId: string }> {
  return api.post<{ jobId: string }>("/api/instances/deploy", params);
}

// GET /api/instances/deploy/{jobId}
export async function getDeployStatus(jobId: string): Promise<DeployJob> {
  return api.get<DeployJob>(`/api/instances/deploy/${jobId}`);
}

export async function overview(): Promise<import("@/types/models").InstanceOverview> {
  return api.get<import("@/types/models").InstanceOverview>("/api/instances/overview");
}

export async function renameInstance(id: string, name: string): Promise<InstanceListView> {
  return api.post<InstanceListView>(`/api/instances/${id}/rename`, { name });
}

export async function archiveInstance(id: string, archived: boolean): Promise<InstanceListView> {
  return api.post<InstanceListView>(`/api/instances/${id}/archive`, { archived });
}

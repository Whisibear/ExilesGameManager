
import { api } from "./httpClient";
import type { AppUpdateStatus } from "@/types/models";
export function getStatus(force = false): Promise<AppUpdateStatus> { return api.get<AppUpdateStatus>(`/api/app-update${force ? "?force=true" : ""}`); }
export function install(): Promise<{ ok: boolean; version: string; message: string }> { return api.post("/api/app-update/install"); }

import { api } from "./httpClient";
import type { SystemSettings } from "@/types/models";

// GET /api/system-settings
export async function getSystemSettings(): Promise<SystemSettings> {
  return api.get<SystemSettings>("/api/system-settings");
}

// POST /api/system-settings
export async function updateSystemSettings(settings: SystemSettings): Promise<SystemSettings> {
  return api.post<SystemSettings>("/api/system-settings", settings);
}

export interface DiagnosticsResult {
  reportPath: string;
  report: string;
}

// POST /api/system-settings/diagnostics
export async function runDiagnostics(forceAdmin: boolean = false): Promise<DiagnosticsResult> {
  return api.post<DiagnosticsResult>("/api/system-settings/diagnostics", { forceAdmin });
}


export interface DiagnosticPackageResult {
  packagePath: string;
  fileName: string;
  downloadUrl: string;
}

export async function createDiagnosticPackage(): Promise<DiagnosticPackageResult> {
  return api.post<DiagnosticPackageResult>("/api/system-settings/diagnostics/package");
}

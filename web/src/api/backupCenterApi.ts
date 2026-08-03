import { api } from "./httpClient";
import type { BackupCenterResponse, BackupRecord, BackupVerifyResult, BackupRestoreResult } from "@/types/models";

export async function listAllBackups(): Promise<BackupCenterResponse> {
  return api.get<BackupCenterResponse>("/api/backup-center");
}
export async function runInstanceBackup(instanceId: string): Promise<BackupRecord> {
  return api.post<BackupRecord>(`/api/backup-center/${instanceId}/run`);
}
export async function verifyInstanceBackup(instanceId: string, timestamp: string): Promise<BackupVerifyResult> {
  return api.post<BackupVerifyResult>(`/api/backup-center/${instanceId}/${encodeURIComponent(timestamp)}/verify`);
}
export async function restoreInstanceBackup(instanceId: string, timestamp: string): Promise<BackupRestoreResult> {
  return api.post<BackupRestoreResult>(`/api/backup-center/${instanceId}/${encodeURIComponent(timestamp)}/restore`);
}
export async function deleteInstanceBackup(instanceId: string, timestamp: string): Promise<{ deleted: boolean }> {
  return api.delete<{ deleted: boolean }>(`/api/backup-center/${instanceId}/${encodeURIComponent(timestamp)}`);
}
export function backupCenterExportUrl(instanceId: string, timestamp: string): string {
  return `/api/backup-center/${instanceId}/${encodeURIComponent(timestamp)}/export`;
}

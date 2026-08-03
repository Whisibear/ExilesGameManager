import { api } from "./httpClient";
import type { TaskQueueResponse, QueueTask } from "@/types/models";

export async function listTasks(params?: { instanceId?: string; status?: string; limit?: number }): Promise<TaskQueueResponse> {
  const query = new URLSearchParams();
  if (params?.instanceId) query.set("instanceId", params.instanceId);
  if (params?.status) query.set("status", params.status);
  if (params?.limit) query.set("limit", String(params.limit));
  const suffix = query.size ? `?${query.toString()}` : "";
  return api.get<TaskQueueResponse>(`/api/tasks${suffix}`);
}

export async function getTask(id: string): Promise<QueueTask> {
  return api.get<QueueTask>(`/api/tasks/${id}`);
}

export async function cancelTask(id: string): Promise<QueueTask> {
  return api.post<QueueTask>(`/api/tasks/${id}/cancel`);
}

export async function pauseTask(id: string): Promise<QueueTask> {
  return api.post<QueueTask>(`/api/tasks/${id}/pause`);
}

export async function resumeTask(id: string): Promise<QueueTask> {
  return api.post<QueueTask>(`/api/tasks/${id}/resume`);
}

export async function retryTask(id: string): Promise<QueueTask> {
  return api.post<QueueTask>(`/api/tasks/${id}/retry`);
}

export async function clearCompleted(): Promise<{ deleted: number }> {
  return api.delete<{ deleted: number }>("/api/tasks/completed");
}

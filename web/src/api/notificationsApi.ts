import { api } from "./httpClient";
import type { NotificationCenterResponse } from "@/types/models";
export const list = (unreadOnly=false, limit=100) => api.get<NotificationCenterResponse>(`/api/notifications?unreadOnly=${unreadOnly}&limit=${limit}`);
export const markRead = (id:string) => api.post<{ok:boolean}>(`/api/notifications/${id}/read`);
export const markAllRead = () => api.post<{updated:number}>("/api/notifications/read-all");
export const clearRead = () => api.delete<{deleted:number}>("/api/notifications/read");

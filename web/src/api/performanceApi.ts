import { api } from "./httpClient";
import type { PerformanceSnapshot, InstancePerformanceResponse } from "@/types/models";
export async function getActivePerformance(): Promise<PerformanceSnapshot> {
  return api.get<PerformanceSnapshot>("/api/performance/active");
}
export async function getAllInstancePerformance(): Promise<InstancePerformanceResponse> {
  return api.get<InstancePerformanceResponse>("/api/performance/instances");
}

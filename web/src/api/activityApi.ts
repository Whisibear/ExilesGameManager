import { api } from "./httpClient";
import type { ActivityCenterResponse } from "@/types/models";
export async function list(params: {instanceId?:string; category?:string; level?:string; q?:string; limit?:number} = {}) {
 const query=new URLSearchParams(); Object.entries(params).forEach(([k,v])=>{if(v!==undefined&&v!=="all"&&v!=="")query.set(k,String(v));});
 return api.get<ActivityCenterResponse>(`/api/activity${query.size?`?${query}`:""}`);
}

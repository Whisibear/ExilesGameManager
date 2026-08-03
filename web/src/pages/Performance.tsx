import * as React from "react";
import { useTranslation } from "react-i18next";
import { Activity, Cpu, HardDrive, MemoryStick, Network } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { StatTile } from "@/components/fantasy/StatTile";
import { EgmProgress } from "@/components/ui/egm-progress";
import * as performanceApi from "@/api/performanceApi";
import type { PerformanceSnapshot } from "@/types/models";
import { formatUptime } from "@/lib/format";

const gb=(v:number)=>`${(v/1024/1024/1024).toFixed(2)} GB`;
const rate=(v:number)=>v>=1024*1024?`${(v/1024/1024).toFixed(1)} MB/s`:`${(v/1024).toFixed(1)} KB/s`;
export default function Performance(){
 const {t}=useTranslation(); const [data,setData]=React.useState<PerformanceSnapshot|null>(null); const [error,setError]=React.useState("");
 React.useEffect(()=>{let alive=true; const load=()=>performanceApi.getActivePerformance().then(v=>alive&&setData(v)).catch(e=>alive&&setError(String(e))); load(); const tick=()=>{if(document.visibilityState==="visible")load();}; const id=setInterval(tick,5000); document.addEventListener("visibilitychange",tick); return()=>{alive=false;clearInterval(id);document.removeEventListener("visibilitychange",tick)}},[]);
 if(!data)return <div className="p-8 text-parchment-300/60">{error||t("performance.loading",{defaultValue:"Loading live performance data..."})}</div>;
 return <div className="space-y-6">
  <Panel icon={<Activity/>} title={t("performance.title",{defaultValue:"Performance Monitor"})}>
   <div className="flex flex-wrap gap-4 text-sm text-parchment-300/70"><span>{data.instanceName}</span><span>{data.state}</span><span>{t("performance.uptime",{defaultValue:"Uptime"})}: {formatUptime(data.uptimeSeconds)}</span><span>{t("performance.refresh",{defaultValue:"Live refresh: 2 seconds"})}</span></div>
  </Panel>
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
   <StatTile icon={<Cpu/>} label={t("performance.serverCpu",{defaultValue:"Server CPU"})} value={`${data.serverCpuPercent.toFixed(1)}%`} accent="arcane"><EgmProgress value={data.serverCpuPercent} variant="arcane" className="mt-3"/></StatTile>
   <StatTile icon={<MemoryStick/>} label={t("performance.serverRam",{defaultValue:"Server RAM"})} value={gb(data.serverRamBytes)} accent="mana"/>
   <StatTile icon={<Cpu/>} label={t("performance.systemCpu",{defaultValue:"System CPU"})} value={`${data.systemCpuPercent.toFixed(1)}%`} hint={`${data.physicalCpuCount}/${data.logicalCpuCount} cores`} accent="gold"><EgmProgress value={data.systemCpuPercent} variant="gold" className="mt-3"/></StatTile>
   <StatTile icon={<MemoryStick/>} label={t("performance.systemRam",{defaultValue:"System RAM"})} value={gb(data.systemRamUsedBytes)} hint={t("performance.ofTotal",{defaultValue:"of {{total}}",total:gb(data.systemRamTotalBytes)})} accent="life"><EgmProgress value={data.systemRamPercent} variant="life" className="mt-3"/></StatTile>
  </div>
  <div className="grid gap-4 md:grid-cols-2">
   <Panel icon={<HardDrive/>} title={t("performance.storage",{defaultValue:"Storage"})}><div className="space-y-3 text-sm"><EgmProgress value={data.diskPercent} variant="gold" label={`${gb(data.diskUsedBytes)} / ${gb(data.diskTotalBytes)}`} valueLabel={`${data.diskPercent.toFixed(1)}%`}/><div className="flex justify-between text-parchment-300/70"><span>{t("performance.read",{defaultValue:"Read"})}: {rate(data.diskReadBytesPerSecond)}</span><span>{t("performance.write",{defaultValue:"Write"})}: {rate(data.diskWriteBytesPerSecond)}</span></div></div></Panel>
   <Panel icon={<Network/>} title={t("performance.network",{defaultValue:"Network"})}><div className="grid grid-cols-2 gap-4 text-sm"><div><p className="text-parchment-300/50">{t("performance.download",{defaultValue:"Download"})}</p><p className="text-lg text-parchment-100">{rate(data.networkDownloadBytesPerSecond)}</p></div><div><p className="text-parchment-300/50">{t("performance.upload",{defaultValue:"Upload"})}</p><p className="text-lg text-parchment-100">{rate(data.networkUploadBytesPerSecond)}</p></div></div></Panel>
  </div>
 </div>
}

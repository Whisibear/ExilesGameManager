import * as React from "react";
import { ChevronDown, ChevronUp, RefreshCw, Search, Server, Settings, ListChecks } from "lucide-react";
import { useTranslation } from "react-i18next";
import { activityApi, instancesApi } from "@/api";
import type { ActivityEvent, InstanceListView } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";

export default function ActivityCenter() {
  const { t, i18n } = useTranslation();
  const [events, setEvents] = React.useState<ActivityEvent[]>([]);
  const [instances, setInstances] = React.useState<InstanceListView | null>(null);
  const [instanceId, setInstanceId] = React.useState("all");
  const [category, setCategory] = React.useState("all");
  const [level, setLevel] = React.useState("all");
  const [q, setQ] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set());

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const r = await activityApi.list({ instanceId: instanceId === "all" ? undefined : instanceId, category, level, q, limit: 250 });
      setEvents(r.events);
    } finally {
      setLoading(false);
    }
  }, [instanceId, category, level, q]);

  React.useEffect(() => { instancesApi.list().then(setInstances).catch(() => undefined); }, []);
  React.useEffect(() => {
    void load();
    const tick = () => { if (document.visibilityState === "visible") void load(); };
    const timer = window.setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", tick); };
  }, [load]);

  const icon = (c: string) => c === "task" ? ListChecks : c === "application" ? Settings : Server;
  const toggle = (id: string) => setExpanded(current => { const next = new Set(current); next.has(id) ? next.delete(id) : next.add(id); return next; });

  return <div className="space-y-5">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div><h2 className="font-display text-2xl font-semibold text-parchment-100">{t("activityCenter.title")}</h2><p className="mt-1 text-sm text-parchment-300/60">{t("activityCenter.description")}</p></div>
      <ActionButton size="sm" icon={<RefreshCw className={loading ? "animate-spin" : ""}/>} onClick={() => void load()}>{t("common.refresh", { defaultValue: "Refresh" })}</ActionButton>
    </div>
    <Panel><div className="grid gap-3 p-4 md:grid-cols-[1fr_12rem_12rem_12rem]"><label className="relative"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-parchment-300/45"/><input value={q} onChange={e=>setQ(e.target.value)} placeholder={t("activityCenter.search")} className="w-full rounded-lg border border-stone-700 bg-stone-900/65 py-2.5 pl-10 pr-3 text-sm text-parchment-100 outline-none focus:border-mana-500"/></label><select value={category} onChange={e=>setCategory(e.target.value)} className="rounded-lg border border-stone-700 bg-stone-900/65 px-3 text-sm"><option value="all">{t("activityCenter.categories.all")}</option><option value="server">{t("activityCenter.categories.server")}</option><option value="task">{t("activityCenter.categories.task")}</option><option value="application">{t("activityCenter.categories.application")}</option></select><select value={level} onChange={e=>setLevel(e.target.value)} className="rounded-lg border border-stone-700 bg-stone-900/65 px-3 text-sm"><option value="all">{t("activityCenter.levels.all")}</option>{["info","warning","error","debug"].map(v=><option key={v} value={v}>{t(`activityCenter.levels.${v}`)}</option>)}</select><select value={instanceId} onChange={e=>setInstanceId(e.target.value)} className="rounded-lg border border-stone-700 bg-stone-900/65 px-3 text-sm"><option value="all">{t("activityCenter.allServers")}</option>{instances?.instances.map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</select></div></Panel>
    <Panel title={t("activityCenter.timeline")}><div className="divide-y divide-stone-700/60">{events.length===0?<div className="p-10 text-center text-sm text-parchment-300/55">{t("activityCenter.empty")}</div>:events.map(e=>{const Icon=icon(e.category);const open=expanded.has(e.id);return <div key={e.id} className="flex gap-4 p-4"><div className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border ${e.level==="error"?"border-blood-500/40 text-blood-300":e.level==="warning"?"border-yellow-500/40 text-yellow-300":e.category==="task"?"border-life-500/40 text-life-300":"border-mana-500/40 text-mana-300"}`}><Icon className="h-4 w-4"/></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="font-medium text-parchment-100">{e.sourceKey?t(e.sourceKey,{defaultValue:e.source}):e.source}</p><time className="text-[11px] text-parchment-300/40">{new Date(typeof e.timestamp==="number"?e.timestamp*1000:e.timestamp).toLocaleString(i18n.language)}</time></div><p className="mt-1 whitespace-pre-wrap text-sm text-parchment-300/70">{e.message}</p>{e.technicalDetails&&<div className="mt-3"><button type="button" onClick={()=>toggle(e.id)} className="inline-flex items-center gap-1 text-xs font-medium text-mana-300 hover:text-mana-200">{open?<ChevronUp className="h-3.5 w-3.5"/>:<ChevronDown className="h-3.5 w-3.5"/>}{t("activityCenter.technicalDetails",{defaultValue:"Technical details"})}</button>{open&&<pre className="mt-2 max-h-72 overflow-auto rounded-lg border border-stone-700 bg-black/35 p-3 text-xs leading-5 text-parchment-300/70">{e.technicalDetails}</pre>}</div>}<div className="mt-2 flex gap-2 text-[10px] uppercase tracking-wide text-parchment-300/40"><span>{t(`activityCenter.categories.${e.category}`)}</span><span>·</span><span>{t(`activityCenter.levels.${e.level}`)}</span></div></div></div>})}</div></Panel>
  </div>;
}

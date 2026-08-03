import * as React from "react";
import { useTranslation } from "react-i18next";
import {
  Ban, CheckCircle2, CirclePause, CirclePlay, Clock3, Eraser, LoaderCircle,
  RefreshCcw, RotateCcw, Search, XCircle,
} from "lucide-react";
import { tasksApi, instancesApi } from "@/api";
import type { InstanceListView, QueueTask, QueueTaskStatus } from "@/types/models";
import { ActionButton } from "@/components/ui/egm-button";
import { Panel } from "@/components/ui/panel";
import { EgmProgress } from "@/components/ui/egm-progress";
import { cn } from "@/lib/utils";

const ACTIVE = new Set<QueueTaskStatus>(["queued", "running", "paused", "cancelling"]);

function formatDate(value: number | null, locale: string): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(locale, { dateStyle: "short", timeStyle: "medium" }).format(new Date(value * 1000));
}

function statusIcon(status: QueueTaskStatus) {
  if (status === "completed") return CheckCircle2;
  if (status === "failed" || status === "cancelled") return XCircle;
  if (status === "paused") return CirclePause;
  if (status === "running" || status === "cancelling") return LoaderCircle;
  return Clock3;
}

export default function TaskQueue() {
  const { t, i18n } = useTranslation();
  const [tasks, setTasks] = React.useState<QueueTask[]>([]);
  const [instances, setInstances] = React.useState<InstanceListView | null>(null);
  const [status, setStatus] = React.useState<string>("all");
  const [instanceId, setInstanceId] = React.useState<string>("all");
  const [query, setQuery] = React.useState("");
  const [selected, setSelected] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(async () => {
    const [taskRows, instanceRows] = await Promise.all([
      tasksApi.listTasks({ status: status === "all" ? undefined : status, instanceId: instanceId === "all" ? undefined : instanceId }),
      instancesApi.list(),
    ]);
    setTasks(taskRows.tasks);
    setInstances(instanceRows);
  }, [status, instanceId]);

  React.useEffect(() => {
    let disposed = false;
    let timer = 0;
    async function tick() {
      try { await load(); } catch { /* normal transient network state */ }
      if (!disposed) timer = window.setTimeout(tick, 2000);
    }
    void tick();
    return () => { disposed = true; window.clearTimeout(timer); };
  }, [load]);

  const filtered = React.useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return tasks;
    return tasks.filter((task) => `${task.title} ${task.action} ${task.message} ${task.id}`.toLowerCase().includes(needle));
  }, [tasks, query]);

  const selectedTask = tasks.find((task) => task.id === selected) ?? null;
  const nameFor = (id: string | null) => instances?.instances.find((item) => item.id === id)?.name ?? t("taskQueue.global");

  async function mutate(action: () => Promise<unknown>) {
    setBusy(true);
    try { await action(); await load(); } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6 p-5 lg:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold text-parchment-100">{t("taskQueue.title")}</h2>
          <p className="mt-1 max-w-3xl text-sm text-parchment-300/65">{t("taskQueue.description")}</p>
        </div>
        <div className="flex gap-2">
          <ActionButton size="sm" icon={<RefreshCcw />} onClick={() => void load()}>{t("common.refresh", { defaultValue: "Refresh" })}</ActionButton>
          <ActionButton size="sm" variant="danger" icon={<Eraser />} onClick={() => mutate(tasksApi.clearCompleted)}>{t("taskQueue.clearCompleted")}</ActionButton>
        </div>
      </div>

      <Panel>
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_13rem_13rem]">
          <label className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-parchment-300/45" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("taskQueue.searchPlaceholder")} className="w-full rounded-lg border border-stone-700 bg-stone-900/65 py-2.5 pl-10 pr-3 text-sm text-parchment-100 outline-none focus:border-mana-500" />
          </label>
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded-lg border border-stone-700 bg-stone-900/65 px-3 text-sm text-parchment-100">
            <option value="all">{t("taskQueue.filters.allStatuses")}</option>
            {["queued","running","paused","cancelling","completed","failed","cancelled"].map((item) => <option key={item} value={item}>{t(`taskQueue.status.${item}`)}</option>)}
          </select>
          <select value={instanceId} onChange={(event) => setInstanceId(event.target.value)} className="rounded-lg border border-stone-700 bg-stone-900/65 px-3 text-sm text-parchment-100">
            <option value="all">{t("taskQueue.filters.allServers")}</option>
            {instances?.instances.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </div>
      </Panel>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_28rem]">
        <Panel title={t("taskQueue.queueTitle")}>
          <div className="divide-y divide-stone-700/60">
            {filtered.length === 0 && <div className="p-8 text-center text-sm text-parchment-300/55">{t("taskQueue.empty")}</div>}
            {filtered.map((task) => {
              const Icon = statusIcon(task.status);
              const active = ACTIVE.has(task.status);
              return (
                <button key={task.id} onClick={() => setSelected(task.id)} className={cn("w-full p-4 text-left transition-colors hover:bg-mana-500/[0.035]", selected === task.id && "bg-mana-500/[0.06]")}> 
                  <div className="flex items-start gap-3">
                    <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", task.status === "completed" ? "text-life-400" : task.status === "failed" ? "text-red-400" : task.status === "cancelled" ? "text-parchment-300/45" : "text-mana-400", active && task.status === "running" && "animate-spin")} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="truncate font-medium text-parchment-100">{task.title}</p>
                        <span className="rounded-full border border-stone-700 px-2 py-0.5 text-[10px] uppercase tracking-wide text-parchment-300/60">{t(`taskQueue.status.${task.status}`)}</span>
                      </div>
                      <p className="mt-1 text-xs text-parchment-300/55">{nameFor(task.instanceId)} · {task.action}</p>
                      <div className="mt-3"><EgmProgress value={task.progress} /></div>
                      <div className="mt-2 flex justify-between text-[11px] text-parchment-300/45"><span>{task.message}</span><span>{Math.round(task.progress)}%</span></div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </Panel>

        <Panel title={t("taskQueue.detailsTitle")}>
          {!selectedTask ? <div className="p-8 text-center text-sm text-parchment-300/55">{t("taskQueue.selectTask")}</div> : (
            <div className="space-y-4 p-4">
              <div>
                <h3 className="font-semibold text-parchment-100">{selectedTask.title}</h3>
                <p className="mt-1 break-all font-mono text-[11px] text-mana-300/70">{selectedTask.id}</p>
              </div>
              <dl className="grid grid-cols-2 gap-3 text-xs">
                <div><dt className="text-parchment-300/45">{t("taskQueue.server")}</dt><dd className="mt-1 text-parchment-100">{nameFor(selectedTask.instanceId)}</dd></div>
                <div><dt className="text-parchment-300/45">{t("taskQueue.priority")}</dt><dd className="mt-1 text-parchment-100">{selectedTask.priority}</dd></div>
                <div><dt className="text-parchment-300/45">{t("taskQueue.created")}</dt><dd className="mt-1 text-parchment-100">{formatDate(selectedTask.createdAt, i18n.language)}</dd></div>
                <div><dt className="text-parchment-300/45">{t("taskQueue.started")}</dt><dd className="mt-1 text-parchment-100">{formatDate(selectedTask.startedAt, i18n.language)}</dd></div>
              </dl>
              <div className="flex flex-wrap gap-2">
                {selectedTask.status === "running" && <ActionButton size="sm" disabled={busy} icon={<CirclePause />} onClick={() => mutate(() => tasksApi.pauseTask(selectedTask.id))}>{t("taskQueue.actions.pause")}</ActionButton>}
                {selectedTask.status === "paused" && <ActionButton size="sm" disabled={busy} icon={<CirclePlay />} onClick={() => mutate(() => tasksApi.resumeTask(selectedTask.id))}>{t("taskQueue.actions.resume")}</ActionButton>}
                {ACTIVE.has(selectedTask.status) && <ActionButton size="sm" variant="danger" disabled={busy} icon={<Ban />} onClick={() => mutate(() => tasksApi.cancelTask(selectedTask.id))}>{t("taskQueue.actions.cancel")}</ActionButton>}
                {(["failed","cancelled","completed"] as QueueTaskStatus[]).includes(selectedTask.status) && <ActionButton size="sm" disabled={busy} icon={<RotateCcw />} onClick={() => mutate(() => tasksApi.retryTask(selectedTask.id))}>{t("taskQueue.actions.retry")}</ActionButton>}
              </div>
              {selectedTask.error && <div className="rounded-lg border border-red-500/30 bg-red-500/[0.06] p-3 text-xs text-red-200">{selectedTask.error}</div>}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-parchment-300/50">{t("taskQueue.liveLog")}</p>
                <div className="max-h-[28rem] space-y-1 overflow-auto rounded-lg border border-stone-700 bg-abyss-950/75 p-3 font-mono text-[11px]">
                  {selectedTask.log.length === 0 && <p className="text-parchment-300/35">{t("taskQueue.noLog")}</p>}
                  {selectedTask.log.map((entry, index) => <p key={`${entry.timestamp}-${index}`} className={cn(entry.level === "error" ? "text-red-300" : entry.level === "warning" ? "text-yellow-300" : entry.level === "debug" ? "text-parchment-300/45" : "text-parchment-200")}><span className="text-mana-400/55">[{new Date(entry.timestamp * 1000).toLocaleTimeString(i18n.language)}]</span> {entry.message}</p>)}
                </div>
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

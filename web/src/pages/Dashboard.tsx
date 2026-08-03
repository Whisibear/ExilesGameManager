import * as React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Activity,
  ArchiveRestore,
  BookOpen,
  Cpu,
  Gauge,
  HardDrive,
  LayoutDashboard,
  Map,
  MemoryStick,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  Server,
  Settings2,
  ShieldCheck,
  Square,
  Tag,
  Users,
} from "lucide-react";
import { PlayersSection } from "@/components/players/PlayersSection";
import { useServerStatus } from "@/hooks/useServerStatus";
import { useAuth } from "@/hooks/useAuth";
import { activityApi, backupCenterApi, instancesApi, modsApi, serverApi, tasksApi } from "@/api";
import type { ActivityEvent, QueueTask, ServerInstance } from "@/types/models";
import { formatUptime, formatRelativeTime } from "@/lib/format";
import { EgmProgress } from "@/components/ui/egm-progress";
import { ActionButton } from "@/components/ui/egm-button";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const [instance, setInstance] = React.useState<ServerInstance | null | undefined>(undefined);
  const neutral = sessionStorage.getItem("egm-neutral-dashboard") === "true";

  React.useEffect(() => {
    if (neutral) {
      setInstance(null);
      return;
    }
    instancesApi.getActive().then(setInstance).catch(() => setInstance(null));
  }, [neutral]);

  if (instance === undefined) {
    return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-mana-600/25 border-t-mana-400" /></div>;
  }

  if (!instance || neutral) return <NeutralDashboard />;
  return <ActiveDashboard instance={instance} />;
}

function NeutralDashboard() {
  const { t } = useTranslation();
  return (
    <div className="grid min-h-[calc(100vh-9rem)] place-items-center">
      <section className="w-full max-w-3xl rounded-2xl border border-mana-500/25 bg-gradient-to-br from-mana-500/[0.055] via-[#111923]/95 to-life-500/[0.025] p-8 text-center shadow-[0_28px_80px_rgba(0,0,0,.32)] sm:p-12">
        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-2xl border border-mana-500/30 bg-mana-500/[0.08] text-mana-300 shadow-egm-cyan"><LayoutDashboard className="h-9 w-9" /></div>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[.22em] text-mana-300">Exiles Game Manager</p>
        <h2 className="mt-3 font-display text-3xl font-semibold text-parchment-100">{t("dashboard.selectServerTitle", { defaultValue: "Select a server to continue" })}</h2>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-parchment-300/60">{t("dashboard.selectServerDescription", { defaultValue: "Choose an existing server, import an installation, or deploy a new dedicated server before opening its management dashboard." })}</p>
        <div className="mt-7 flex justify-center"><Link to="/servers"><ActionButton variant="mana" icon={<Server />}>{t("dashboard.noServerCta", { defaultValue: "Open all servers" })}</ActionButton></Link></div>
      </section>
    </div>
  );
}

function ActiveDashboard({ instance }: { instance: ServerInstance }) {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { status, loading } = useServerStatus(4000);
  const [modCount, setModCount] = React.useState<number | null>(null);
  const [tasks, setTasks] = React.useState<QueueTask[]>([]);
  const [activity, setActivity] = React.useState<ActivityEvent[]>([]);
  const [working, setWorking] = React.useState<string | null>(null);

  const loadSecondary = React.useCallback(async () => {
    const [mods, taskData, activityData] = await Promise.all([
      modsApi.getMods().catch(() => []),
      tasksApi.listTasks({ instanceId: instance.id, limit: 4 }).catch(() => ({ tasks: [] })),
      activityApi.list({ instanceId: instance.id, limit: 5 }).catch(() => ({ events: [] })),
    ]);
    setModCount(mods.length);
    setTasks(taskData.tasks);
    setActivity(activityData.events);
  }, [instance.id]);

  React.useEffect(() => {
    void loadSecondary();
    const tick = () => { if (document.visibilityState === "visible") void loadSecondary(); };
    const timer = window.setInterval(tick, 15000);
    document.addEventListener("visibilitychange", tick);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", tick); };
  }, [loadSecondary]);

  async function runAction(action: string, callback: () => Promise<unknown>) {
    setWorking(action);
    try { await callback(); } finally { setWorking(null); }
  }

  if (loading || !status) return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-mana-600/25 border-t-mana-400" /></div>;

  const ramPercent = status.ramTotalGB > 0 ? (status.ramUsedGB / status.ramTotalGB) * 100 : 0;
  const systemRamPercent = status.ramTotalGB > 0 ? (status.systemRamUsedGB / status.ramTotalGB) * 100 : 0;
  const playersPercent = status.maxPlayers > 0 ? (status.playersOnline / status.maxPlayers) * 100 : 0;
  const runningTasks = tasks.filter((task) => ["queued", "running", "paused", "cancelling"].includes(task.status));
  const online = status.state === "online";

  return (
    <div className="space-y-5">
      <section className="relative overflow-hidden rounded-2xl border border-stone-700/75 bg-gradient-to-br from-[#151e29]/95 via-[#101720]/95 to-[#0b1118]/95 p-6 shadow-[0_22px_60px_rgba(0,0,0,.28)]">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-mana-400/75 to-transparent" />
        <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-mana-400/[0.045] blur-3xl" />
        <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-center">
          <div className="flex min-w-0 items-start gap-4">
            <div className={cn("mt-1 flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border", online ? "border-life-500/30 bg-life-500/[0.08] text-life-300 shadow-egm-lime" : "border-stone-600/75 bg-white/[0.025] text-parchment-300/50")}><Server className="h-7 w-7" /></div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="truncate font-display text-2xl font-semibold text-parchment-100">{instance.name}</h2>
                <span className={cn("inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide", online ? "border-life-500/30 bg-life-500/[0.07] text-life-300" : "border-stone-600/70 bg-white/[0.025] text-parchment-300/55")}><span className={cn("h-2 w-2 rounded-full", online ? "bg-life-400 shadow-[0_0_10px_rgba(124,252,0,.65)]" : "bg-stone-500")} />{t(`serverControl.states.${status.state}`, { defaultValue: status.state })}</span>
              </div>
              <p className="mt-2 text-sm text-parchment-300/50">Palworld Dedicated Server · UDP {instance.gamePort}</p>
              <div className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-4">
                <SummaryLine icon={<Users />} label={t("dashboard.stats.players", { defaultValue: "Players" })} value={`${status.playersOnline}/${status.maxPlayers}`} />
                <SummaryLine icon={<Map />} label={t("dashboard.map", { defaultValue: "Map" })} value={status.map || "-"} />
                <SummaryLine icon={<Gauge />} label={t("dashboard.uptime", { defaultValue: "Uptime" })} value={formatUptime(status.uptimeSeconds)} />
                <SummaryLine icon={<Save />} label={t("dashboard.lastSaved", { defaultValue: "Last saved" })} value={status.lastSavedAt ? formatRelativeTime(status.lastSavedAt) : t("dashboard.never", { defaultValue: "Never" })} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-2">
            <QuickAction icon={<Play />} label={t("serverControl.actions.start", { defaultValue: "Start" })} disabled={online || working !== null} onClick={() => void runAction("start", serverApi.startServer)} tone="life" />
            <QuickAction icon={<Square />} label={t("serverControl.actions.stop", { defaultValue: "Stop" })} disabled={!online || working !== null} onClick={() => void runAction("stop", serverApi.stopServer)} tone="danger" />
            <QuickAction icon={<RotateCcw />} label={t("serverControl.actions.restart", { defaultValue: "Restart" })} disabled={!online || working !== null} onClick={() => void runAction("restart", serverApi.restartServer)} tone="mana" />
            <QuickAction icon={<ArchiveRestore />} label={t("backupCenter.backupNow", { defaultValue: "Backup" })} disabled={working !== null} onClick={() => void runAction("backup", () => backupCenterApi.runInstanceBackup(instance.id))} tone="arcane" />
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <MetricCard icon={<Cpu />} label={t("dashboard.stats.cpu", { defaultValue: "CPU" })} value={`${Math.round(status.cpuPercent)}%`} accent="mana"><EgmProgress value={status.cpuPercent} variant="mana" className="mt-4" /></MetricCard>
        <MetricCard icon={<MemoryStick />} label={t("dashboard.stats.ram", { defaultValue: "RAM" })} value={`${status.ramUsedGB.toFixed(1)} GB`} hint={`${status.ramTotalGB.toFixed(1)} GB total`} accent="arcane"><EgmProgress value={ramPercent} variant="arcane" className="mt-4" /></MetricCard>
        <MetricCard icon={<HardDrive />} label={t("dashboard.stats.systemRam", { defaultValue: "System RAM" })} value={`${status.systemRamUsedGB.toFixed(1)} GB`} accent="life"><EgmProgress value={systemRamPercent} variant="life" className="mt-4" /></MetricCard>
        <MetricCard icon={<Users />} label={t("dashboard.stats.players", { defaultValue: "Players" })} value={`${status.playersOnline}/${status.maxPlayers}`} accent="life"><EgmProgress value={playersPercent} variant="life" className="mt-4" /></MetricCard>
        <MetricCard icon={<Tag />} label={t("dashboard.stats.version", { defaultValue: "Version" })} value={status.serverVersion || "-"} hint={t("dashboard.stats.versionHint", { defaultValue: "Server build" })} accent="mana" />
        <MetricCard icon={<BookOpen />} label={t("dashboard.stats.mods", { defaultValue: "Mods" })} value={modCount ?? "-"} hint={t("dashboard.stats.modsHint", { defaultValue: "Installed mods" })} accent="arcane" />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,.8fr)]">
        <Panel title={t("dashboard.recentActivity", { defaultValue: "Recent activity" })} icon={<Activity />} action={<Link to="/activity" className="text-xs font-medium text-mana-300 hover:text-mana-200">{t("common.viewAll", { defaultValue: "View all" })}</Link>}>
          <div className="divide-y divide-stone-700/55">
            {activity.length ? activity.map((event) => <div key={event.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0"><span className={cn("mt-1 h-2 w-2 shrink-0 rounded-full", event.level === "error" ? "bg-blood-400" : event.level === "warning" ? "bg-amber-400" : "bg-mana-400")} /><div className="min-w-0"><p className="truncate text-sm font-medium text-parchment-100">{event.source}</p><p className="mt-0.5 line-clamp-2 text-xs leading-5 text-parchment-300/50">{event.message}</p></div><time className="ml-auto shrink-0 text-[10px] text-parchment-300/30">{new Date(event.timestamp).toLocaleTimeString()}</time></div>) : <EmptyState label={t("dashboard.noActivity", { defaultValue: "No recent activity." })} />}
          </div>
        </Panel>

        <Panel title={t("dashboard.runningTasks", { defaultValue: "Running tasks" })} icon={<RefreshCw />} action={user.role === "super_admin" ? <Link to="/tasks" className="text-xs font-medium text-mana-300 hover:text-mana-200">{t("common.viewAll", { defaultValue: "View all" })}</Link> : undefined}>
          <div className="space-y-3">
            {runningTasks.length ? runningTasks.slice(0, 4).map((task) => <div key={task.id} className="rounded-xl border border-stone-700/65 bg-black/10 p-3"><div className="flex items-center justify-between gap-3"><p className="truncate text-sm font-medium text-parchment-100">{task.title}</p><span className="font-mono text-xs text-mana-300">{Math.round(task.progress)}%</span></div><EgmProgress value={task.progress} variant={task.status === "paused" ? "arcane" : "mana"} className="mt-3" /><p className="mt-2 truncate text-xs text-parchment-300/40">{task.message}</p></div>) : <EmptyState label={t("dashboard.noRunningTasks", { defaultValue: "No active background tasks." })} />}
          </div>
        </Panel>
      </section>

      <Panel title={t("dashboard.quickLinks", { defaultValue: "Management shortcuts" })} icon={<Settings2 />}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <DashboardLink to="/control" icon={<Server />} title={t("nav.control")} description={t("dashboard.links.control", { defaultValue: "Start, stop, restart, save, and update." })} />
          <DashboardLink to="/mods" icon={<BookOpen />} title={t("nav.mods")} description={t("dashboard.links.mods", { defaultValue: "Manage Steam Workshop, Nexus, and UE4SS." })} />
          <DashboardLink to="/backup-center" icon={<ArchiveRestore />} title={t("nav.backupCenter")} description={t("dashboard.links.backups", { defaultValue: "Create, verify, restore, and export backups." })} />
          <DashboardLink to="/firewall" icon={<ShieldCheck />} title={t("nav.firewall")} description={t("dashboard.links.firewall", { defaultValue: "Inspect and synchronize Windows Firewall rules." })} />
        </div>
      </Panel>

      <PlayersSection />
    </div>
  );
}

function SummaryLine({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return <div className="flex min-w-0 items-center gap-2"><span className="shrink-0 text-mana-400 [&_svg]:h-4 [&_svg]:w-4">{icon}</span><div className="min-w-0"><p className="text-[10px] uppercase tracking-wider text-parchment-300/35">{label}</p><p className="truncate font-medium text-parchment-100">{value}</p></div></div>;
}

function QuickAction({ icon, label, disabled, onClick, tone }: { icon: React.ReactNode; label: string; disabled?: boolean; onClick: () => void; tone: "life" | "danger" | "mana" | "arcane" }) {
  const styles = { life: "hover:border-life-500/45 hover:text-life-300", danger: "hover:border-blood-500/45 hover:text-blood-300", mana: "hover:border-mana-500/45 hover:text-mana-300", arcane: "hover:border-arcane-500/45 hover:text-arcane-300" };
  return <button disabled={disabled} onClick={onClick} className={cn("flex min-w-[120px] items-center gap-2 rounded-xl border border-stone-700/70 bg-white/[0.025] px-4 py-3 text-sm font-semibold text-parchment-200 transition disabled:cursor-not-allowed disabled:opacity-35", styles[tone])}><span className="[&_svg]:h-4 [&_svg]:w-4">{icon}</span>{label}</button>;
}

function MetricCard({ icon, label, value, hint, accent, children }: { icon: React.ReactNode; label: string; value: React.ReactNode; hint?: React.ReactNode; accent: "mana" | "life" | "arcane"; children?: React.ReactNode }) {
  const style = accent === "life" ? "text-life-400 border-life-500/20" : accent === "arcane" ? "text-arcane-400 border-arcane-500/20" : "text-mana-400 border-mana-500/20";
  return <article className="rounded-2xl border border-stone-700/70 bg-gradient-to-br from-[#151d27]/92 to-[#0c1219]/92 p-4 shadow-[0_14px_36px_rgba(0,0,0,.2)]"><div className="flex items-center gap-2.5"><span className={cn("flex h-9 w-9 items-center justify-center rounded-xl border bg-black/15 [&_svg]:h-4 [&_svg]:w-4", style)}>{icon}</span><p className="text-[10px] font-semibold uppercase tracking-[.14em] text-parchment-300/40">{label}</p></div><p className="mt-4 truncate font-display text-2xl font-bold text-parchment-100">{value}</p>{hint && <p className="mt-1 truncate text-xs text-parchment-300/38">{hint}</p>}{children}</article>;
}

function Panel({ title, icon, action, children }: { title: string; icon: React.ReactNode; action?: React.ReactNode; children: React.ReactNode }) {
  return <section className="overflow-hidden rounded-2xl border border-stone-700/70 bg-gradient-to-br from-[#141c26]/94 to-[#0b1118]/94 shadow-[0_18px_48px_rgba(0,0,0,.22)]"><header className="flex items-center justify-between gap-3 border-b border-stone-700/60 px-5 py-4"><div className="flex items-center gap-3"><span className="text-mana-400 [&_svg]:h-4 [&_svg]:w-4">{icon}</span><h3 className="font-display text-sm font-semibold uppercase tracking-[.1em] text-parchment-100">{title}</h3></div>{action}</header><div className="p-5">{children}</div></section>;
}

function DashboardLink({ to, icon, title, description }: { to: string; icon: React.ReactNode; title: string; description: string }) {
  return <Link to={to} className="group rounded-xl border border-stone-700/65 bg-black/10 p-4 transition hover:-translate-y-0.5 hover:border-mana-500/35 hover:bg-mana-500/[0.035]"><div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl border border-mana-500/20 bg-mana-500/[0.06] text-mana-300 transition group-hover:border-mana-400/40 [&_svg]:h-4 [&_svg]:w-4">{icon}</span><p className="font-semibold text-parchment-100">{title}</p></div><p className="mt-3 text-xs leading-5 text-parchment-300/45">{description}</p></Link>;
}

function EmptyState({ label }: { label: string }) { return <p className="py-8 text-center text-sm text-parchment-300/40">{label}</p>; }

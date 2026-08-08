import * as React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Activity, FolderInput, Gauge, HardDrive, LayoutDashboard, LogOut, Map, Plus, RefreshCw, Save, Server, Users } from "lucide-react";
import { instancesApi } from "@/api";
import type { InstanceOverview } from "@/types/models";
import { DeployServerWizard } from "@/components/settings/DeployServerWizard";
import { ImportServerDialog } from "@/components/settings/ImportServerDialog";
import { formatUptime } from "@/lib/format";
import { ActionButton } from "@/components/ui/egm-button";
import { cn } from "@/lib/utils";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { useAuth } from "@/hooks/useAuth";

function formatSaved(value: string, neverLabel: string, locale: string) {
  if (!value) return neverLabel;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? neverLabel : date.toLocaleString(locale);
}

export default function ServerSelection() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const [data, setData] = React.useState<InstanceOverview | null>(null);
  const [deployOpen, setDeployOpen] = React.useState(false);
  const [importOpen, setImportOpen] = React.useState(false);
  const load = React.useCallback(() => instancesApi.overview().then(setData), []);

  React.useEffect(() => {
    void load();
    const tick = () => { if (document.visibilityState === "visible") void load(); };
    const timer = window.setInterval(tick, 10000);
    document.addEventListener("visibilitychange", tick);
    return () => { window.clearInterval(timer); document.removeEventListener("visibilitychange", tick); };
  }, [load]);

  async function openServer(id: string) {
    sessionStorage.removeItem("egm-neutral-dashboard");
    await instancesApi.setActive(id);
    navigate("/dashboard");
  }

  function openNeutralDashboard() {
    sessionStorage.setItem("egm-neutral-dashboard", "true");
    navigate("/dashboard");
  }

  const servers = data?.instances.filter((item) => !item.archived) ?? [];
  const neverLabel = t("serverSelection.never");
  const onlineCount = servers.filter((server) => server.state === "online").length;
  const totalPlayers = servers.reduce((sum, server) => sum + server.playersOnline, 0);

  return (
    <div className="min-h-screen bg-noise">
      <header className="sticky top-0 z-20 border-b border-stone-700/65 bg-[#0a1118]/90 backdrop-blur-xl">
        <div className="mx-auto flex min-h-20 max-w-[1780px] items-center justify-between gap-4 px-5 py-3 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <img src="/branding/egm-icon-64.png" alt="EGM" className="h-11 w-11 shrink-0 drop-shadow-[0_0_16px_rgba(0,212,255,.28)]" />
            <div className="min-w-0">
              <p className="truncate font-display text-sm font-bold tracking-[.08em] text-parchment-100 sm:text-base">EXILES GAME MANAGER</p>
              <p className="truncate text-[10px] font-semibold uppercase tracking-[.2em] text-mana-300/65">Professional Self-Hosted Server Management</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <LanguageSwitcher />
            <div className="hidden items-center gap-2 rounded-lg border border-stone-700/70 bg-white/[0.025] px-3 py-2 text-xs text-parchment-300/60 md:flex">
              <span className="max-w-[120px] truncate">{user.username}</span>
              <button onClick={() => logout()} className="text-parchment-300/45 transition hover:text-blood-300" title={t("topbar.userMenu.logOut")}><LogOut className="h-4 w-4" /></button>
            </div>
            <ActionButton variant="ghost" size="sm" icon={<LayoutDashboard />} onClick={openNeutralDashboard}>{t("serverSelection.dashboard")}</ActionButton>
            <ActionButton variant="mana" size="sm" icon={<FolderInput />} onClick={() => setImportOpen(true)}>{t("serverSelection.importServer")}</ActionButton>
            <ActionButton variant="ghost" size="sm" icon={<RefreshCw />} onClick={() => void load()}>{t("common.refresh")}</ActionButton>
            <ActionButton variant="life" size="sm" icon={<Plus />} onClick={() => setDeployOpen(true)}>{t("serverSelection.newServer")}</ActionButton>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1780px] px-5 py-8 lg:px-8 lg:py-10">
        <section className="mb-7 grid gap-5 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[.22em] text-mana-300">{t("serverSelection.eyebrow")}</p>
            <h1 className="font-display text-3xl font-semibold text-parchment-100 sm:text-4xl">{t("serverSelection.title")}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-parchment-300/60">{t("serverSelection.subtitle")}</p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <SummaryMetric icon={<Server />} label={t("serverSelection.summary.servers", { defaultValue: "Servers" })} value={servers.length} />
            <SummaryMetric icon={<Activity />} label={t("serverSelection.summary.online", { defaultValue: "Online" })} value={onlineCount} accent="life" />
            <SummaryMetric icon={<Users />} label={t("serverSelection.summary.players", { defaultValue: "Players" })} value={totalPlayers} accent="mana" />
          </div>
        </section>

        {servers.length ? (
          <section className="grid gap-5 md:grid-cols-2 2xl:grid-cols-3">
            {servers.map((item) => {
              const isOnline = item.state === "online";
              return (
                <article key={item.id} className="group relative overflow-hidden rounded-2xl border border-stone-700/75 bg-gradient-to-br from-[#151d27]/95 via-[#101720]/95 to-[#0b1118]/95 p-5 shadow-[0_18px_50px_rgba(0,0,0,.25)] transition duration-200 hover:-translate-y-1 hover:border-mana-500/35 hover:shadow-[0_24px_60px_rgba(0,0,0,.32),0_0_30px_rgba(0,212,255,.06)]">
                  <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-mana-400/60 to-transparent" />
                  <div className="mb-5 flex items-start justify-between gap-4">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-mana-500/25 bg-mana-500/[0.07] text-mana-300"><Server className="h-5 w-5" /></div>
                      <div className="min-w-0">
                        <h2 className="truncate font-display text-lg font-semibold text-parchment-100">{item.name}</h2>
                        <p className="mt-1 truncate text-xs text-parchment-300/45">{item.gameLabel} Dedicated Server · UDP {item.gamePort}</p>
                      </div>
                    </div>
                    <span className={cn("inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide", isOnline ? "border-life-500/30 bg-life-500/[0.07] text-life-300" : "border-stone-600/70 bg-white/[0.025] text-parchment-300/55")}>
                      <span className={cn("h-2 w-2 rounded-full", isOnline ? "bg-life-400 shadow-[0_0_10px_rgba(124,252,0,.65)]" : "bg-stone-500")} />
                      {t(`serverControl.states.${item.state}`, { defaultValue: item.state })}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <ServerMetric icon={<Users />} label={t("serverSelection.players")} value={`${item.playersOnline}/${item.maxPlayers}`} />
                    <ServerMetric icon={<Map />} label={t("serverSelection.map")} value={item.map || "-"} />
                    <ServerMetric icon={<Gauge />} label={t("serverSelection.uptime")} value={formatUptime(item.uptimeSeconds)} />
                    <ServerMetric icon={<Save />} label={t("serverSelection.lastSave")} value={formatSaved(item.lastSavedAt, neverLabel, i18n.language)} />
                  </div>

                  <div className="mt-5 flex items-center justify-between gap-3 border-t border-stone-700/65 pt-4">
                    <span className="flex items-center gap-2 text-xs text-parchment-300/40"><HardDrive className="h-4 w-4 text-arcane-400" />{t("serverSelection.managedInstance", { defaultValue: "Managed instance" })}</span>
                    <ActionButton variant="mana" size="sm" onClick={() => void openServer(item.id)}>{t("serverSelection.openDashboard", { defaultValue: "Open dashboard" })}</ActionButton>
                  </div>
                </article>
              );
            })}
          </section>
        ) : (
          <section className="rounded-2xl border border-dashed border-mana-500/25 bg-gradient-to-br from-mana-500/[0.04] via-white/[0.015] to-life-500/[0.025] px-6 py-16 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-mana-500/30 bg-mana-500/[0.08] text-mana-300 shadow-egm-cyan"><Server className="h-8 w-8" /></div>
            <h2 className="mt-5 font-display text-2xl font-semibold text-parchment-100">{t("serverSelection.emptyTitle")}</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-parchment-300/60">{t("serverSelection.empty")}</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <ActionButton variant="mana" icon={<FolderInput />} onClick={() => setImportOpen(true)}>{t("serverSelection.importServer")}</ActionButton>
              <ActionButton variant="life" icon={<Plus />} onClick={() => setDeployOpen(true)}>{t("serverSelection.newServer")}</ActionButton>
            </div>
          </section>
        )}
      </main>

      <DeployServerWizard open={deployOpen} onOpenChange={setDeployOpen} onDeployed={load} />
      <ImportServerDialog open={importOpen} onOpenChange={setImportOpen} onImported={load} />
    </div>
  );
}

function SummaryMetric({ icon, label, value, accent = "mana" }: { icon: React.ReactNode; label: string; value: React.ReactNode; accent?: "mana" | "life" }) {
  return <div className="min-w-[108px] rounded-xl border border-stone-700/70 bg-white/[0.025] p-3"><div className={cn("mb-2 [&_svg]:h-4 [&_svg]:w-4", accent === "life" ? "text-life-400" : "text-mana-400")}>{icon}</div><p className="font-display text-xl font-bold text-parchment-100">{value}</p><p className="mt-0.5 text-[10px] uppercase tracking-wider text-parchment-300/40">{label}</p></div>;
}

function ServerMetric({ icon, label, value }: { icon: React.ReactNode; label: string; value: React.ReactNode }) {
  return <div className="rounded-xl border border-stone-700/65 bg-black/10 p-3"><div className="flex items-center gap-2 text-xs text-parchment-300/45"><span className="text-mana-400 [&_svg]:h-4 [&_svg]:w-4">{icon}</span>{label}</div><p className="mt-2 truncate text-sm font-semibold text-parchment-100">{value}</p></div>;
}

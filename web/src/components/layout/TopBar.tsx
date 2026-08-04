import * as React from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Users, Server as ServerIcon, ChevronDown, Plus, UserCircle2, LogOut, ArrowUpCircle, Cpu, MemoryStick, Loader2, ExternalLink, RefreshCw, X } from "lucide-react";
import { useServerStatus } from "@/hooks/useServerStatus";
import { useAuth } from "@/hooks/useAuth";
import { instancesApi, appUpdateApi } from "@/api";
import type { InstanceListView, AppUpdateStatus } from "@/types/models";
import { DeployServerWizard } from "@/components/settings/DeployServerWizard";
import { LanguageSwitcher } from "@/components/layout/LanguageSwitcher";
import { NotificationBell } from "@/components/layout/NotificationBell";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

const PAGE_KEYS: Record<string, string> = {
  "/": "servers", "/servers": "servers", "/dashboard": "dashboard", "/mods": "mods", "/control": "control",
  "/world-settings": "worldSettings", "/performance": "performance", "/tasks": "taskQueue", "/activity": "activity",
  "/backup-center": "backupCenter", "/firewall": "firewall", "/university": "university", "/launcher-options": "launcherOptions",
  "/logs": "logs", "/settings": "settings", "/super-admin": "superAdmin", "/mod-wishlist": "modWishlist",
};

function UpdateAvailableBadge() {
  const { t } = useTranslation();
  const [status, setStatus] = React.useState<AppUpdateStatus | null>(null);
  const [open, setOpen] = React.useState(false);
  const [checking, setChecking] = React.useState(false);
  const [installing, setInstalling] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async (force = false) => {
    setChecking(true);
    setError(null);
    try {
      setStatus(await appUpdateApi.getStatus(force));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setChecking(false);
    }
  }, []);

  React.useEffect(() => {
    void load(false);
    const timer = window.setInterval(() => void load(true), 5 * 60 * 1000);
    return () => window.clearInterval(timer);
  }, [load]);

  async function installUpdate() {
    if (!status?.updateAvailable) return;
    if (!status.installerAvailable || !status.installSupported) {
      if (status.releaseUrl) window.open(status.releaseUrl, "_blank", "noopener,noreferrer");
      return;
    }
    setInstalling(true);
    setError(null);
    try {
      await appUpdateApi.install();
    } catch (reason) {
      setInstalling(false);
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  }

  if (!status?.updateAvailable) return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="hidden items-center gap-2 rounded-lg border border-life-500/35 bg-life-500/[0.08] px-3 py-2 text-xs font-semibold text-life-200 transition hover:border-life-400/60 hover:bg-life-500/[0.14] lg:flex"
      >
        <ArrowUpCircle className="h-4 w-4" />
        <span>{t("updates.headerAvailable", { defaultValue: "New update available" })}</span>
        <span className="rounded bg-life-500/15 px-1.5 py-0.5 font-mono text-[10px]">{status.latestVersion}</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-mana-500/35 bg-[#0a1119] shadow-2xl shadow-black/60">
            <div className="flex items-start justify-between border-b border-stone-700/60 px-5 py-4">
              <div>
                <p className="text-[11px] uppercase tracking-[.18em] text-mana-300/70">{t("updates.dialogEyebrow", { defaultValue: "Exiles Game Manager Update" })}</p>
                <h2 className="mt-1 text-xl font-semibold text-parchment-100">{t("updates.dialogTitle", { version: status.latestVersion, defaultValue: `Install ${status.latestVersion}?` })}</h2>
              </div>
              <button type="button" onClick={() => setOpen(false)} disabled={installing} className="rounded-md p-1.5 text-parchment-300/50 transition hover:bg-white/5 hover:text-parchment-100"><X className="h-4 w-4" /></button>
            </div>

            <div className="space-y-4 px-5 py-5">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-stone-700/60 bg-black/15 p-3"><p className="text-[10px] uppercase tracking-[.16em] text-parchment-300/45">{t("updates.currentVersion", { defaultValue: "Installed version" })}</p><p className="mt-1 font-mono text-sm text-parchment-100">{status.currentVersion}</p></div>
                <div className="rounded-lg border border-life-500/25 bg-life-500/[0.05] p-3"><p className="text-[10px] uppercase tracking-[.16em] text-life-300/60">{t("updates.latestVersion", { defaultValue: "Available version" })}</p><p className="mt-1 font-mono text-sm text-life-200">{status.latestVersion}</p></div>
              </div>
              <div className="rounded-lg border border-mana-500/20 bg-mana-500/[0.05] p-4 text-sm leading-relaxed text-parchment-200/75">{t("updates.automaticFlow", { defaultValue: "EGM downloads the verified installer, closes all EGM processes, updates the existing installation and starts EGM again automatically. Settings, OAuth data, servers and backups remain unchanged." })}</div>
              {error && <div className="rounded-lg border border-red-500/30 bg-red-500/[0.07] p-3 text-sm text-red-200">{error}</div>}
            </div>

            <div className="flex flex-wrap justify-end gap-2 border-t border-stone-700/60 px-5 py-4">
              {status.releaseUrl && <button type="button" disabled={installing} onClick={() => window.open(status.releaseUrl!, "_blank", "noopener,noreferrer")} className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-parchment-200 transition hover:bg-white/5"><ExternalLink className="h-4 w-4" />{t("updates.releaseNotes", { defaultValue: "Release page" })}</button>}
              <button type="button" disabled={checking || installing} onClick={() => void load(true)} className="inline-flex items-center gap-2 rounded-lg border border-stone-600/80 px-3 py-2 text-sm text-parchment-100 transition hover:border-mana-500/50 disabled:opacity-50">{checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}{t("updates.checkAgain", { defaultValue: "Check again" })}</button>
              <button type="button" disabled={installing} onClick={() => void installUpdate()} className="inline-flex items-center gap-2 rounded-lg border border-life-500/40 bg-life-500/[0.1] px-3 py-2 text-sm font-semibold text-life-200 transition hover:bg-life-500/[0.16] disabled:opacity-50">{installing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUpCircle className="h-4 w-4" />}{installing ? t("updates.preparingInstall", { defaultValue: "Preparing update…" }) : t("updates.installAndRestart", { defaultValue: "Update and restart" })}</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function InstanceSwitcher() {
  const { t } = useTranslation();
  const [data, setData] = React.useState<InstanceListView | null>(null);
  const [deployOpen, setDeployOpen] = React.useState(false);
  const neutralDashboard = sessionStorage.getItem("egm-neutral-dashboard") === "true";

  React.useEffect(() => {
    let cancelled = false;
    let timer: number;
    async function tick() {
      const next = await instancesApi.list();
      if (cancelled) return;
      setData(next);
      if (next.instances.length === 0) timer = window.setTimeout(tick, 3000);
    }
    void tick();
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, []);

  async function handleSwitch(id: string) {
    sessionStorage.removeItem("egm-neutral-dashboard");
    if (id !== data?.activeId) await instancesApi.setActive(id);
    window.location.reload();
  }

  const active = neutralDashboard ? undefined : data?.instances.find((item) => item.id === data.activeId);
  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex min-w-[150px] max-w-[260px] items-center gap-2 rounded-lg border border-mana-500/30 bg-[#101923]/90 px-3 py-2 text-sm font-semibold text-parchment-100 shadow-[0_0_24px_rgba(0,212,255,.06)] transition hover:border-mana-400/55">
            <ServerIcon className="h-4 w-4 shrink-0 text-mana-300" />
            <span className="truncate">{active?.name ?? t("topbar.instanceSwitcher.noServerSelected")}</span>
            <ChevronDown className="ml-auto h-4 w-4 shrink-0 text-parchment-300/50" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-[240px]">
          {data?.instances.length ? data.instances.map((instance) => (
            <DropdownMenuItem key={instance.id} onSelect={() => void handleSwitch(instance.id)}>
              {instance.id === data.activeId && !neutralDashboard ? "✓ " : ""}{instance.name}
            </DropdownMenuItem>
          )) : <DropdownMenuItem disabled>{t("topbar.instanceSwitcher.noServersYet")}</DropdownMenuItem>}
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => setDeployOpen(true)}><Plus className="h-4 w-4" />{t("topbar.instanceSwitcher.newServer")}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <DeployServerWizard open={deployOpen} onOpenChange={setDeployOpen} onDeployed={() => window.location.reload()} />
    </>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-lg border border-stone-700/70 bg-white/[0.025] px-3 py-2 text-xs text-parchment-200 transition hover:border-mana-500/35">
          <UserCircle2 className="h-4 w-4 text-mana-300" /><span className="hidden max-w-[110px] truncate md:inline">{user.username}</span><ChevronDown className="h-3.5 w-3.5 opacity-55" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled>{user.role === "super_admin" ? t("topbar.userMenu.superAdmin") : t("topbar.userMenu.admin")}</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem destructive onSelect={() => logout()}><LogOut className="h-4 w-4" />{t("topbar.userMenu.logOut")}</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function TopBar() {
  const location = useLocation();
  const { status } = useServerStatus();
  const { t } = useTranslation();
  const pageKey = PAGE_KEYS[location.pathname] ?? "dashboard";
  const neutralDashboard = sessionStorage.getItem("egm-neutral-dashboard") === "true";
  const titleKey = `topbar.pages.${pageKey}.title`;
  const subtitleKey = `topbar.pages.${pageKey}.subtitle`;

  return (
    <header className="sticky top-0 z-20 flex min-h-20 items-center justify-between gap-4 border-b border-stone-700/65 bg-[#0b121a]/88 px-4 py-3 shadow-[0_12px_34px_rgba(0,0,0,.2)] backdrop-blur-xl sm:px-6 lg:px-8">
      <div className="min-w-0">
        <h1 className="truncate font-display text-lg font-semibold tracking-[.04em] text-parchment-100 sm:text-xl">
          {t(titleKey, { defaultValue: t(`nav.${pageKey}`, { defaultValue: "Exiles Game Manager" }) })}
        </h1>
        <p className="mt-0.5 hidden truncate text-xs text-parchment-300/45 sm:block">{t(subtitleKey, { defaultValue: "" })}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <UpdateAvailableBadge />
        <NotificationBell />
        <InstanceSwitcher />
        {status && !neutralDashboard && (
          <div className="hidden items-center gap-3 rounded-lg border border-stone-700/65 bg-white/[0.025] px-3 py-2 2xl:flex">
            <span className="flex items-center gap-1.5 font-mono text-xs text-parchment-200"><Users className="h-3.5 w-3.5 text-life-400" />{status.playersOnline}/{status.maxPlayers}</span>
            <span className="h-4 w-px bg-stone-700" />
            <span className="flex items-center gap-1.5 font-mono text-xs text-parchment-300/70"><Cpu className="h-3.5 w-3.5 text-mana-400" />{Math.round(status.cpuPercent)}%</span>
            <span className="flex items-center gap-1.5 font-mono text-xs text-parchment-300/70"><MemoryStick className="h-3.5 w-3.5 text-arcane-400" />{status.ramUsedGB.toFixed(1)} GB</span>
          </div>
        )}
        <LanguageSwitcher />
        <UserMenu />
      </div>
    </header>
  );
}

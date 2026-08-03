import * as React from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Users, Server as ServerIcon, ChevronDown, Plus, UserCircle2, LogOut, ArrowUpCircle, Cpu, MemoryStick, Loader2 } from "lucide-react";
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
  const [installing, setInstalling] = React.useState(false);
  React.useEffect(() => {
    let cancelled = false;
    const load = async () => { try { const next = await appUpdateApi.getStatus(); if (!cancelled) setStatus(next); } catch {} };
    void load();
    const timer = window.setInterval(load, 5 * 60 * 1000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, []);
  if (!status?.updateAvailable) return null;
  async function installUpdate() {
    if (!status?.installerAvailable || !status.installSupported) { if (status?.releaseUrl) window.open(status.releaseUrl, "_blank", "noopener,noreferrer"); return; }
    if (!window.confirm(t("updates.confirmInstall", { version: status.latestVersion, defaultValue: `Install EGM ${status.latestVersion} now? EGM will close automatically.` }))) return;
    setInstalling(true);
    try { await appUpdateApi.install(); } catch (error) { setInstalling(false); window.alert(error instanceof Error ? error.message : String(error)); }
  }
  return <button onClick={() => void installUpdate()} disabled={installing} className="hidden items-center gap-2 rounded-lg border border-life-500/25 bg-life-500/[0.06] px-3 py-2 text-xs font-medium text-life-300 transition hover:border-life-400/45 hover:bg-life-500/[0.1] disabled:opacity-60 xl:flex">{installing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUpCircle className="h-4 w-4" />}{installing ? t("updates.installing", { defaultValue: "Installing update…" }) : t("updates.available", { version: status.latestVersion, defaultValue: `EGM ${status.latestVersion} available` })}</button>;
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

import * as React from "react";
import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import {
  Activity,
  ArchiveRestore,
  BellRing,
  BookOpen,
  Crown,
  GraduationCap,
  Heart,
  LayoutDashboard,
  ListChecks,
  Rocket,
  ScrollText,
  Server,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Swords,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { appUpdateApi } from "@/api";
import type { AppUpdateStatus } from "@/types/models";

interface NavigationItem {
  to: string;
  labelKey: string;
  icon: typeof Server;
  end?: boolean;
  superAdminOnly?: boolean;
}

const NAVIGATION_GROUPS: Array<{ key: string; items: NavigationItem[] }> = [
  {
    key: "servers",
    items: [
      { to: "/servers", labelKey: "allServers", icon: Server, end: true },
      { to: "/dashboard", labelKey: "dashboard", icon: LayoutDashboard },
    ],
  },
  {
    key: "server",
    items: [
      { to: "/control", labelKey: "control", icon: Swords },
      { to: "/world-settings", labelKey: "worldSettings", icon: SlidersHorizontal },
      { to: "/mods", labelKey: "mods", icon: BookOpen },
    ],
  },
  {
    key: "operations",
    items: [
      { to: "/tasks", labelKey: "taskQueue", icon: ListChecks, superAdminOnly: true },
      { to: "/activity", labelKey: "activity", icon: BellRing },
      { to: "/logs", labelKey: "logs", icon: ScrollText },
    ],
  },
  {
    key: "maintenance",
    items: [
      { to: "/backup-center", labelKey: "backupCenter", icon: ArchiveRestore, superAdminOnly: true },
      { to: "/firewall", labelKey: "firewall", icon: ShieldCheck, superAdminOnly: true },
      { to: "/performance", labelKey: "performance", icon: Activity },
    ],
  },
  {
    key: "administration",
    items: [
      { to: "/mod-wishlist", labelKey: "modWishlist", icon: Heart, superAdminOnly: true },
      { to: "/launcher-options", labelKey: "launcherOptions", icon: Rocket, superAdminOnly: true },
      { to: "/settings", labelKey: "settings", icon: Settings2, superAdminOnly: true },
      { to: "/super-admin", labelKey: "superAdmin", icon: Crown, superAdminOnly: true },
      { to: "/university", labelKey: "university", icon: GraduationCap },
    ],
  },
];

function NavItem({ item }: { item: NavigationItem }) {
  const { t } = useTranslation();
  return (
    <NavLink to={item.to} end={item.end}>
      {({ isActive }) => (
        <div
          className={cn(
            "group relative flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-all",
            isActive ? "text-parchment-100" : "text-parchment-300/65 hover:bg-white/[0.035] hover:text-parchment-100"
          )}
        >
          {isActive && (
            <motion.div
              layoutId="sidebar-active"
              className="absolute inset-0 rounded-lg border border-mana-500/30 bg-gradient-to-r from-mana-500/[0.13] via-mana-500/[0.045] to-transparent shadow-[inset_3px_0_0_#00d4ff,0_0_22px_rgba(0,212,255,.06)]"
              transition={{ type: "spring", stiffness: 360, damping: 32 }}
            />
          )}
          <item.icon
            className={cn(
              "relative h-[18px] w-[18px] shrink-0 transition-colors",
              isActive ? "text-mana-300" : "text-parchment-300/45 group-hover:text-mana-300"
            )}
          />
          <span className="relative hidden min-w-0 flex-1 truncate lg:block">{t(`nav.${item.labelKey}`)}</span>
          {item.superAdminOnly && (
            <Crown className="relative hidden h-3 w-3 shrink-0 text-life-400/55 lg:block" />
          )}
        </div>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [updateStatus, setUpdateStatus] = React.useState<AppUpdateStatus | null>(null);

  React.useEffect(() => {
    appUpdateApi.getStatus().then(setUpdateStatus).catch(() => undefined);
  }, []);

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-[76px] flex-col border-r border-stone-700/70 bg-[#0b1118]/95 shadow-[18px_0_50px_rgba(0,0,0,.2)] backdrop-blur-xl lg:w-64">
      <div className="flex h-20 items-center border-b border-stone-700/70 px-3 lg:px-5">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/branding/egm-icon-64.png" alt="EGM" className="h-10 w-10 shrink-0 drop-shadow-[0_0_14px_rgba(0,212,255,.28)]" />
          <div className="hidden min-w-0 lg:block">
            <p className="truncate font-display text-[13px] font-bold tracking-[.08em] text-parchment-100">EXILES GAME MANAGER</p>
            <p className="mt-0.5 truncate text-[9px] font-semibold uppercase tracking-[.2em] text-mana-300/75">Server Management</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-4 lg:px-3">
        <div className="space-y-5">
          {NAVIGATION_GROUPS.map((group) => {
            const items = group.items.filter((item) => !item.superAdminOnly || user.role === "super_admin");
            if (!items.length) return null;
            return (
              <section key={group.key}>
                <p className="mb-1.5 hidden px-3 text-[10px] font-semibold uppercase tracking-[.18em] text-parchment-300/30 lg:block">
                  {t(`nav.groups.${group.key}`, { defaultValue: group.key })}
                </p>
                <div className="space-y-0.5">{items.map((item) => <NavItem key={item.to} item={item} />)}</div>
              </section>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-stone-700/70 p-3">
        <a
          href="https://www.paypal.com/donate/?hosted_button_id=G6B4H3F9PVXSW"
          target="_blank"
          rel="noopener noreferrer"
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-stone-700/70 bg-white/[0.02] px-3 py-2 text-xs text-parchment-300/45 transition hover:border-mana-500/30 hover:text-mana-300 lg:justify-start"
        >
          <Heart className="h-4 w-4" />
          <span className="hidden lg:inline">{t("nav.donate", { defaultValue: "Support the project" })}</span>
        </a>
        <p className="mt-2 hidden px-1 text-[10px] text-parchment-300/25 lg:block">EGM · v{updateStatus?.currentVersion ?? "..."}</p>
      </div>
    </aside>
  );
}

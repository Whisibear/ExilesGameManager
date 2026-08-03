import * as React from "react";
import { useTranslation } from "react-i18next";
import { ScrollText, Search, Download, Info, TriangleAlert, Bug, Ban } from "lucide-react";
import { logsApi } from "@/api";
import type { LogEntry, LogLevel } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { EgmToggle } from "@/components/ui/egm-toggle";
import { ActionButton } from "@/components/ui/egm-button";
import { SegmentedTabs, SegmentedTabsList, SegmentedTabsTrigger } from "@/components/ui/segmented-tabs";
import { formatTimestamp } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useNotifications } from "@/hooks/useNotifications";
import { useAuth } from "@/hooks/useAuth";

type LevelFilter = "all" | LogLevel;

const LEVEL_CONFIG: Record<LogLevel, { icon: typeof Info; text: string; border: string; bg: string }> = {
  info: { icon: Info, text: "text-mana-300", border: "border-l-mana-500/50", bg: "" },
  warning: { icon: TriangleAlert, text: "text-life-400", border: "border-l-life-500/60", bg: "bg-life-500/[0.04]" },
  error: { icon: Ban, text: "text-blood-400", border: "border-l-blood-500/70", bg: "bg-blood-500/[0.06]" },
  debug: { icon: Bug, text: "text-parchment-300/40", border: "border-l-stone-600", bg: "" },
};

export default function Logs() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isSuperAdmin = user.role === "super_admin";
  const [activityLogs, setActivityLogs] = React.useState<LogEntry[]>([]);
  const [appLogs, setAppLogs] = React.useState<LogEntry[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [level, setLevel] = React.useState<LevelFilter>("all");
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const notifications = useNotifications();

  React.useEffect(() => {
    logsApi.getLogStreams().then((streams) => {
      setActivityLogs(streams.activity);
      setAppLogs(streams.app);
      setLoading(false);
    });
  }, []);

  React.useEffect(() => {
    if (!autoRefresh) return;
    const id = window.setInterval(() => {
      logsApi.pollLogStreams().then((streams) => {
        setActivityLogs(streams.activity);
        setAppLogs(streams.app);
      });
    }, 5000);
    return () => window.clearInterval(id);
  }, [autoRefresh]);

  const filteredActivity = activityLogs.filter((l) => {
    if (level !== "all" && l.level !== level) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!l.message.toLowerCase().includes(q) && !l.source.toLowerCase().includes(q)) return false;
    }
    return true;
  });
  const filteredAppLogs = appLogs.filter((entry) => {
    if (level !== "all" && entry.level !== level) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!entry.message.toLowerCase().includes(q) && !entry.source.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const errorCount = [...activityLogs, ...appLogs].filter((l) => l.level === "error").length;
  const warningCount = [...activityLogs, ...appLogs].filter((l) => l.level === "warning").length;

  function handleExport() {
    const blob = logsApi.exportLogs(activityLogs, appLogs);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `palworld-server-logs-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    notifications.success({
      title: t("logs.exportedTitle", { defaultValue: "Logs exported" }),
      message: t("logs.exportedMessage", { defaultValue: "The chronicle has been copied to a scroll." }),
    });
  }

  return (
    <div className="space-y-6">
      <Panel
        icon={<ScrollText />}
        title={t("logs.title", { defaultValue: "The Chronicle" })}
        actions={
          <ActionButton variant="gold" size="sm" icon={<Download />} onClick={handleExport}>
            {t("logs.export", { defaultValue: "Export" })}
          </ActionButton>
        }
      >
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative w-full sm:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-parchment-300/40" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t("logs.searchPlaceholder", { defaultValue: "Search logs..." })}
                className="pl-9"
              />
            </div>
            <SegmentedTabs value={level} onValueChange={(v) => setLevel(v as LevelFilter)}>
              <SegmentedTabsList>
                <SegmentedTabsTrigger value="all">{t("logs.levels.all", { defaultValue: "All" })}</SegmentedTabsTrigger>
                <SegmentedTabsTrigger value="info">{t("logs.levels.info", { defaultValue: "Info" })}</SegmentedTabsTrigger>
                <SegmentedTabsTrigger value="warning">
                  {t("logs.levels.warning", { defaultValue: "Warnings" })}
                  {warningCount > 0 && <span className="ml-1 text-life-500">({warningCount})</span>}
                </SegmentedTabsTrigger>
                <SegmentedTabsTrigger value="error">
                  {t("logs.levels.error", { defaultValue: "Errors" })}
                  {errorCount > 0 && <span className="ml-1 text-blood-400">({errorCount})</span>}
                </SegmentedTabsTrigger>
                <SegmentedTabsTrigger value="debug">
                  {t("logs.levels.debug", { defaultValue: "Debug" })}
                </SegmentedTabsTrigger>
              </SegmentedTabsList>
            </SegmentedTabs>
          </div>
          <EgmToggle
            id="auto-refresh"
            checked={autoRefresh}
            onCheckedChange={setAutoRefresh}
            label={t("logs.autoRefresh", { defaultValue: "Auto-refresh" })}
            className="w-fit"
          />
        </div>

        <div className="grid gap-4 xl:grid-cols-2">
          <div className="min-w-0">
            <div className="mb-2 flex items-center justify-between gap-3">
              <h2 className="font-display text-sm font-semibold text-life-300">ExilesGameManager</h2>
              <span className="font-mono text-xs text-parchment-300/40">
                {t("logs.linesCount", { defaultValue: "{{count}} lines", count: filteredAppLogs.length })}
              </span>
            </div>
            {!isSuperAdmin && (
              <p className="mb-2 text-[11px] text-parchment-300/40">
                {t("logs.ipsHiddenHint", {
                  defaultValue: "IP addresses in this output are hidden - only the super admin can see them.",
                })}
              </p>
            )}
            <ScrollArea className="h-[520px] rounded-md border border-stone-700 bg-abyss-950/60">
              {loading ? (
                <div className="flex h-full items-center justify-center text-parchment-300/50">
                  <p className="animate-pulse font-display">
                    {t("logs.loading", { defaultValue: "Unfurling the scroll..." })}
                  </p>
                </div>
              ) : filteredAppLogs.length === 0 ? (
                <div className="flex h-40 items-center justify-center px-4 text-center text-parchment-300/40">
                  <p>{t("logs.noAppOutput", { defaultValue: "No ExilesGameManager output yet." })}</p>
                </div>
              ) : (
                <div className="divide-y divide-stone-800/80 font-mono text-[13px]">
                  {filteredAppLogs.map((entry) => {
                    const config = LEVEL_CONFIG[entry.level];
                    const Icon = config.icon;
                    return (
                      <div
                        key={entry.id}
                        className={cn("flex items-start gap-3 border-l-2 px-4 py-2", config.border, config.bg)}
                      >
                        <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", config.text)} />
                        <span className="shrink-0 text-parchment-300/35">{formatTimestamp(entry.timestamp)}</span>
                        <span className="shrink-0 rounded bg-stone-800/80 px-1.5 py-0.5 text-[11px] text-parchment-300/50">
                          {entry.source}
                        </span>
                        <span className="min-w-0 break-words text-parchment-100/85">{entry.message}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </div>

          <div className="min-w-0">
            <div className="mb-2 flex items-center justify-between gap-3">
              <h2 className="font-display text-sm font-semibold text-life-300">
                {t("logs.serverActivity", { defaultValue: "Server Activity" })}
              </h2>
              <span className="font-mono text-xs text-parchment-300/40">
                {t("logs.entriesCount", { defaultValue: "{{count}} entries", count: filteredActivity.length })}
              </span>
            </div>
            <ScrollArea className="h-[520px] rounded-md border border-stone-700 bg-abyss-950/60">
              {loading ? (
                <div className="flex h-full items-center justify-center text-parchment-300/50">
                  <p className="animate-pulse font-display">
                    {t("logs.loading", { defaultValue: "Unfurling the scroll..." })}
                  </p>
                </div>
              ) : filteredActivity.length === 0 ? (
                <div className="flex h-40 items-center justify-center px-4 text-center text-parchment-300/40">
                  <p>{t("logs.noActivityMatch", { defaultValue: "No server activity matches your search." })}</p>
                </div>
              ) : (
                <div className="divide-y divide-stone-800/80 font-mono text-[13px]">
                  {filteredActivity.map((entry) => {
                    const config = LEVEL_CONFIG[entry.level];
                    const Icon = config.icon;
                    return (
                      <div
                        key={entry.id}
                        className={cn("flex items-start gap-3 border-l-2 px-4 py-2", config.border, config.bg)}
                      >
                        <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", config.text)} />
                        <span className="shrink-0 text-parchment-300/35">{formatTimestamp(entry.timestamp)}</span>
                        <span className="shrink-0 rounded bg-stone-800/80 px-1.5 py-0.5 text-[11px] text-parchment-300/50">
                          {entry.source}
                        </span>
                        <span className={cn("min-w-0 flex-1 break-words", config.text || "text-parchment-200")}>
                          {entry.message}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </Panel>
    </div>
  );
}

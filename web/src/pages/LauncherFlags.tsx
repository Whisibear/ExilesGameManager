import * as React from "react";
import { useTranslation } from "react-i18next";
import { Rocket, Save, ShieldCheck, Router, LockKeyhole } from "lucide-react";
import { instancesApi, networkApi } from "@/api";
import type { ServerInstance, UpnpStatus } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { EgmToggle } from "@/components/ui/egm-toggle";
import { LoadingSkeleton } from "@/components/ui/loading-skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActionButton } from "@/components/ui/egm-button";
import { QuestSpotlight } from "@/components/university/QuestSpotlight";
import { completeQuestStep } from "@/lib/questCompletion";
import { useNotifications } from "@/hooks/useNotifications";

export default function LauncherFlags() {
  const { t } = useTranslation();
  const [instance, setInstance] = React.useState<ServerInstance | null>(null);
  const [networkStatus, setNetworkStatus] = React.useState<UpnpStatus | null>(null);
  const [loaded, setLoaded] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [queryPort, setQueryPort] = React.useState<number | null>(null);
  const [savingQueryPort, setSavingQueryPort] = React.useState(false);
  const notifications = useNotifications();

  const load = React.useCallback(() => {
    setLoaded(false);
    Promise.all([instancesApi.getActive(), networkApi.getUpnpStatus().catch(() => null)])
      .then(([active, status]) => {
        setInstance(active);
        setNetworkStatus(status);
        setQueryPort(active?.queryPort ?? null);
      })
      .finally(() => setLoaded(true));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function saveLaunchOptions(
    nextOptions: Partial<
      Pick<
        ServerInstance,
        | "usePerfThreads"
        | "noAsyncLoadingThread"
        | "useMultithreadForDs"
        | "communityServer"
        | "usePublicIpOverride"
        | "publicIpOverride"
        | "usePublicPortOverride"
        | "useQueryPort"
      >
    >
  ) {
    if (!instance) return;
    setSaving(true);
    try {
      const next = await instancesApi.setLaunchOptions(instance.id, {
        usePerfThreads: "usePerfThreads" in nextOptions ? Boolean(nextOptions.usePerfThreads) : instance.usePerfThreads,
        noAsyncLoadingThread:
          "noAsyncLoadingThread" in nextOptions
            ? Boolean(nextOptions.noAsyncLoadingThread)
            : instance.noAsyncLoadingThread,
        useMultithreadForDs:
          "useMultithreadForDs" in nextOptions
            ? Boolean(nextOptions.useMultithreadForDs)
            : instance.useMultithreadForDs,
        publicLobby: "communityServer" in nextOptions ? Boolean(nextOptions.communityServer) : instance.communityServer,
        usePublicIpOverride:
          "usePublicIpOverride" in nextOptions
            ? Boolean(nextOptions.usePublicIpOverride)
            : instance.usePublicIpOverride,
        publicIpOverride:
          "publicIpOverride" in nextOptions ? String(nextOptions.publicIpOverride ?? "").trim() : instance.publicIpOverride,
        usePublicPortOverride:
          "usePublicPortOverride" in nextOptions
            ? Boolean(nextOptions.usePublicPortOverride)
            : instance.usePublicPortOverride,
        useQueryPort: "useQueryPort" in nextOptions ? Boolean(nextOptions.useQueryPort) : instance.useQueryPort,
      });
      setInstance(next.instances.find((item) => item.id === instance.id) ?? null);
      if ("communityServer" in nextOptions) {
        completeQuestStep("public_choice");
      }
      notifications.success({
        title: t("launcherOptions.savedTitle", { defaultValue: "Launcher options saved" }),
        message: t("launcherOptions.savedMessage", {
          defaultValue: "Restart the server for these launcher options to take effect.",
        }),
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveQueryPort() {
    if (!instance || !instance.useQueryPort || !queryPort || queryPort === publicPortNumber) return;
    setSavingQueryPort(true);
    try {
      const next = await instancesApi.setQueryPort(instance.id, queryPort);
      setInstance(next.instances.find((item) => item.id === instance.id) ?? null);
      notifications.success({
        title: t("launcherOptions.queryPortSavedTitle", { defaultValue: "Steam query port saved" }),
        message: t("launcherOptions.queryPortSavedMessage", {
          defaultValue: "Restart the server for this to take effect.",
        }),
      });
    } catch (e) {
      notifications.error({
        title: t("launcherOptions.queryPortFailedTitle", { defaultValue: "Couldn't save query port" }),
        message:
          e instanceof Error
            ? e.message
            : t("launcherOptions.queryPortFailedMessage", { defaultValue: "The Steam query port could not be saved." }),
      });
    } finally {
      setSavingQueryPort(false);
    }
  }

  function handleQueryPortChange(value: string) {
    const parsed = parseInt(value, 10);
    setQueryPort(Number.isNaN(parsed) ? null : parsed);
  }

  const publicPort = networkStatus?.port ?? instance?.effectiveGamePort ?? instance?.gamePort ?? "";
  const publicPortNumber = typeof publicPort === "number" ? publicPort : parseInt(String(publicPort), 10);
  const queryPortMatchesGame = queryPort !== null && queryPort === publicPortNumber;
  const queryPortInvalid = queryPort !== null && (queryPort < 1 || queryPort > 65535);
  const queryPortDirty = !!instance && queryPort !== null && queryPort !== instance.queryPort;
  const unavailable = t("launcherOptions.unavailable", { defaultValue: "Unavailable" });

  if (!instance) {
    if (!loaded) {
      return (
        <div className="space-y-6 pb-10">
          <Panel icon={<Rocket />} title={t("launcherOptions.title", { defaultValue: "Launcher Options" })}>
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2 rounded-md border border-stone-700 bg-abyss-950/40 p-4">
                  <LoadingSkeleton className="h-4 w-24" />
                  <LoadingSkeleton className="h-3 w-full" />
                </div>
              ))}
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={`wide-${i}`} className="space-y-3 rounded-md border border-stone-700 bg-abyss-950/40 p-4">
                  <LoadingSkeleton className="h-4 w-28" />
                  <LoadingSkeleton className="h-3 w-full" />
                  <LoadingSkeleton className="h-9 w-full" />
                </div>
              ))}
            </div>
          </Panel>
        </div>
      );
    }
    return (
      <div className="flex h-64 items-center justify-center text-parchment-300/50">
        <p className="font-display">
          {t("launcherOptions.selectServer", { defaultValue: "Select a server to edit launcher options." })}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10">
      <Panel icon={<Rocket />} title={t("launcherOptions.title", { defaultValue: "Launcher Options" })}>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2 xl:grid-cols-3">
          <QuestSpotlight stepId="public_choice">
            <EgmToggle
              id="flag-community-server"
              checked={instance.communityServer}
              disabled={saving}
              onCheckedChange={(checked) => saveLaunchOptions({ communityServer: checked })}
              label="-publiclobby"
              description={t("launcherOptions.publicLobby", {
                defaultValue: "Shows the server in Palworld's Community Server list.",
              })}
            />
          </QuestSpotlight>
          <EgmToggle
            id="flag-useperfthreads"
            checked={instance.usePerfThreads}
            disabled={saving}
            onCheckedChange={(checked) => saveLaunchOptions({ usePerfThreads: checked })}
            label="-useperfthreads"
            description={t("launcherOptions.perfThreads", {
              defaultValue: "Enables Palworld's performance-thread launcher path.",
            })}
          />
          <EgmToggle
            id="flag-no-async-loading-thread"
            checked={instance.noAsyncLoadingThread}
            disabled={saving}
            onCheckedChange={(checked) => saveLaunchOptions({ noAsyncLoadingThread: checked })}
            label="-NoAsyncLoadingThread"
            description={t("launcherOptions.noAsyncLoadingThread", {
              defaultValue: "Disables Palworld's separate async loading thread.",
            })}
          />
          <EgmToggle
            id="flag-use-multithread-for-ds"
            checked={instance.useMultithreadForDs}
            disabled={saving}
            onCheckedChange={(checked) => saveLaunchOptions({ useMultithreadForDs: checked })}
            label="-UseMultithreadForDS"
            description={t("launcherOptions.multithreadForDs", {
              defaultValue: "Uses Palworld's dedicated-server multithreading flag.",
            })}
          />
          <div className="space-y-3 rounded-md border border-stone-700 bg-abyss-950/40 p-4">
            <EgmToggle
              id="flag-public-ip"
              checked={instance.usePublicIpOverride}
              disabled={saving}
              onCheckedChange={(checked) => saveLaunchOptions({ usePublicIpOverride: checked })}
              label="-publicip"
              description={t("launcherOptions.publicIpDescription", {
                defaultValue: "Advertises the public IP detected by Super Admin.",
              })}
              className="border-0 bg-transparent p-0"
            />
            <div className={instance.usePublicIpOverride ? "opacity-100" : "opacity-45"}>
              <Label htmlFor="flag-public-ip-value" className="text-[11px]">
                {t("launcherOptions.manualPublicIp", { defaultValue: "Public IP (manual entry)" })}
              </Label>
              <Input
                id="flag-public-ip-value"
                value={instance.publicIpOverride ?? ""}
                placeholder="203.0.113.10"
                disabled={saving || !instance.usePublicIpOverride}
                className="mt-1 font-mono"
                onChange={(event) => setInstance({ ...instance, publicIpOverride: event.target.value })}
                onBlur={() => void saveLaunchOptions({ publicIpOverride: instance.publicIpOverride })}
              />
            </div>
          </div>
          <div className="space-y-3 rounded-md border border-stone-700 bg-abyss-950/40 p-4">
            <EgmToggle
              id="flag-public-port"
              checked={instance.usePublicPortOverride}
              disabled={saving}
              onCheckedChange={(checked) => saveLaunchOptions({ usePublicPortOverride: checked })}
              label="-publicport"
              description={t("launcherOptions.publicPortDescription", {
                defaultValue: "Advertises the game port from Super Admin.",
              })}
              className="border-0 bg-transparent p-0"
            />
            <div className={instance.usePublicPortOverride ? "opacity-60" : "opacity-35"}>
              <Label htmlFor="flag-public-port-value" className="text-[11px]">
                {t("launcherOptions.superAdminGamePort", { defaultValue: "Super Admin game port" })}
              </Label>
              <Input
                id="flag-public-port-value"
                value={publicPort ? String(publicPort) : unavailable}
                disabled
                className="mt-1 font-mono"
              />
            </div>
          </div>
          <div className="space-y-1.5 rounded-md border border-stone-700 bg-abyss-950/40 p-4">
            <EgmToggle
              id="flag-use-query-port"
              checked={instance.useQueryPort}
              disabled={saving}
              onCheckedChange={(checked) => saveLaunchOptions({ useQueryPort: checked })}
              label="-queryport"
              description={t("launcherOptions.queryPortToggleDescription", {
                defaultValue:
                  "Optional Steam server-list/query port. Leave disabled unless you need Steam/community discovery troubleshooting.",
              })}
              className="border-0 bg-transparent p-0"
            />
            <p className="text-[11px] leading-relaxed text-parchment-300/40">
              {t("launcherOptions.queryPortDescription", {
                defaultValue:
                  "When enabled, this must be different from the game port or Palworld can move the game server to the next open port.",
              })}
            </p>
            <div
              className={
                instance.useQueryPort
                  ? "flex flex-wrap items-center gap-2 pt-1"
                  : "flex flex-wrap items-center gap-2 pt-1 opacity-45"
              }
            >
              <Label htmlFor="flag-query-port" className="w-full text-[11px]">
                {t("launcherOptions.queryPortValue", { defaultValue: "Steam query port value" })}
              </Label>
              <Input
                id="flag-query-port"
                type="number"
                min={1}
                max={65535}
                value={queryPort ?? ""}
                onChange={(e) => handleQueryPortChange(e.target.value)}
                className="max-w-[10rem] font-mono"
                disabled={savingQueryPort || !instance.useQueryPort}
              />
              <ActionButton
                type="button"
                variant="gold"
                size="sm"
                icon={<Save />}
                onClick={handleSaveQueryPort}
                disabled={
                  !instance.useQueryPort ||
                  !queryPortDirty ||
                  savingQueryPort ||
                  !queryPort ||
                  queryPortMatchesGame ||
                  queryPortInvalid
                }
              >
                {savingQueryPort
                  ? t("launcherOptions.queryPortSaving", { defaultValue: "Saving..." })
                  : t("launcherOptions.queryPortSave", { defaultValue: "Save Query Port" })}
              </ActionButton>
            </div>
            {queryPortMatchesGame && (
              <p className="text-[11px] text-blood-300">
                {t("launcherOptions.queryPortConflict", {
                  defaultValue:
                    "Use a different port than {{port}}. If they match, Steam query can take the game port first.",
                  port: publicPortNumber,
                })}
              </p>
            )}
            {queryPortInvalid && (
              <p className="text-[11px] text-blood-300">
                {t("launcherOptions.queryPortInvalid", { defaultValue: "Choose a port between 1 and 65535." })}
              </p>
            )}
          </div>
        </div>

        <div className="mt-5 rounded-md border border-life-700/45 bg-abyss-950/55 p-5">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-full border border-life-700/50 bg-life-900/15 p-2 text-life-300">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="font-display text-base text-life-200">
                {t("launcherOptions.firewallNoticeTitle", { defaultValue: "Windows firewall and internet access" })}
              </h3>
              <p className="mt-1 text-sm leading-relaxed text-parchment-300/65">
                {t("launcherOptions.firewallNoticeIntro", {
                  defaultValue:
                    "ExilesGameManager manages only the local Windows Firewall rules for this server instance.",
                })}
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <div className="flex gap-3 rounded-md border border-stone-700/80 bg-black/15 p-4">
              <Router className="mt-0.5 h-5 w-5 shrink-0 text-ember-300" />
              <div>
                <p className="font-display text-sm text-parchment-100">
                  {t("launcherOptions.firewallNoticeRouterTitle", { defaultValue: "Router or hosting provider" })}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-parchment-300/55">
                  {t("launcherOptions.firewallNoticeRouterBody", {
                    defaultValue:
                      "For access from the internet, the Game Port and, when enabled, the Steam Query Port must also be forwarded or allowed in your router, cloud firewall, or dedicated-server provider panel.",
                  })}
                </p>
              </div>
            </div>

            <div className="flex gap-3 rounded-md border border-stone-700/80 bg-black/15 p-4">
              <LockKeyhole className="mt-0.5 h-5 w-5 shrink-0 text-blood-300" />
              <div>
                <p className="font-display text-sm text-parchment-100">
                  {t("launcherOptions.firewallNoticeRestTitle", { defaultValue: "Keep the REST API private" })}
                </p>
                <p className="mt-1 text-xs leading-relaxed text-parchment-300/55">
                  {t("launcherOptions.firewallNoticeRestBody", {
                    defaultValue:
                      "Do not expose the REST API port directly to the public internet when ExilesGameManager uses it locally. Restrict it to localhost or a trusted private network.",
                  })}
                </p>
              </div>
            </div>
          </div>
        </div>

        <p className="mt-4 text-xs text-parchment-300/45">
          {t("launcherOptions.applyNote", {
            defaultValue:
              "These options apply to {{name}} the next time it starts. Public IP and port values are read from Super Admin and cannot be edited here.",
            name: instance.name,
          })}
        </p>
      </Panel>
    </div>
  );
}

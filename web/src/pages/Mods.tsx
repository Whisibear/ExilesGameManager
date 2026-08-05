import * as React from "react";
import { Link } from "react-router-dom";
import { Reorder } from "framer-motion";
import { useTranslation } from "react-i18next";
import { BookOpen, ScrollText, TriangleAlert, RefreshCw, Boxes, Download, CheckCircle2, HardDrive, CircleAlert, ExternalLink, Trash2 } from "lucide-react";
import { modsApi, serverSettingsApi } from "@/api";
import type { Mod, ModsPathInfo, ModWishlistRequest, WorkshopCacheItem, DownloadedNexusMod } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";
import { Modal } from "@/components/ui/modal";
import { EgmToggle } from "@/components/ui/egm-toggle";
import { ModCard } from "@/components/mods/ModCard";
import { WorkshopInstallDialog } from "@/components/mods/WorkshopInstallDialog";
import { NexusBrowseDialog } from "@/components/mods/NexusBrowseDialog";
import { PendingModCard } from "@/components/mods/PendingModCard";
import { Ue4ssPanel } from "@/components/mods/Ue4ssPanel";
import { useNotifications } from "@/hooks/useNotifications";
import { useAuth } from "@/hooks/useAuth";
import { completeQuestStep } from "@/lib/questCompletion";
import { QuestSpotlight } from "@/components/university/QuestSpotlight";

export default function Mods() {
  const { t } = useTranslation();
  const [mods, setMods] = React.useState<Mod[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [removeTarget, setRemoveTarget] = React.useState<Mod | null>(null);
  const [browseOpen, setBrowseOpen] = React.useState(false);
  const [nexusBrowseOpen, setNexusBrowseOpen] = React.useState(false);
  const [wishlist, setWishlist] = React.useState<ModWishlistRequest[]>([]);
  const [updateAllOpen, setUpdateAllOpen] = React.useState(false);
  const [updatingAll, setUpdatingAll] = React.useState(false);
  const [modsPathInfo, setModsPathInfo] = React.useState<ModsPathInfo | null>(null);
  const [allowMods, setAllowMods] = React.useState<boolean | null>(null);
  const [savingAllowMods, setSavingAllowMods] = React.useState(false);
  const [workshopCache, setWorkshopCache] = React.useState<WorkshopCacheItem[]>([]);
  const [cacheLoading, setCacheLoading] = React.useState(false);
  const [cacheBusyId, setCacheBusyId] = React.useState<string | null>(null);
  const [downloadedNexusMods, setDownloadedNexusMods] = React.useState<DownloadedNexusMod[]>([]);
  const [nexusInventoryLoading, setNexusInventoryLoading] = React.useState(false);
  const [nexusInventoryBusyId, setNexusInventoryBusyId] = React.useState<string | null>(null);
  const [nexusUninstallTarget, setNexusUninstallTarget] = React.useState<DownloadedNexusMod | null>(null);
  const seenCacheIds = React.useRef<Set<string>>(new Set());
  const notifications = useNotifications();
  const { user } = useAuth();

  const refreshWorkshopCache = React.useCallback(async (notifyNew = false) => {
    if (user.role !== "super_admin" || document.visibilityState !== "visible") return;
    setCacheLoading(true);
    try {
      const items = await modsApi.getWorkshopCache();
      if (notifyNew && seenCacheIds.current.size > 0) {
        const detected = items.find((item) => !seenCacheIds.current.has(item.workshopId) && item.valid);
        if (detected) {
          notifications.success({
            title: t("mods.cache.detectedTitle", { defaultValue: "Workshop mod detected" }),
            message: t("mods.cache.detectedMessage", { defaultValue: "{{name}} is ready to install.", name: detected.name }),
          });
        }
      }
      seenCacheIds.current = new Set(items.map((item) => item.workshopId));
      setWorkshopCache(items);
    } catch {
      setWorkshopCache([]);
    } finally {
      setCacheLoading(false);
    }
  }, [notifications, t, user.role]);

const refreshDownloadedNexusMods = React.useCallback(async () => {
    if (document.visibilityState !== "visible") return;
    setNexusInventoryLoading(true);
    try {
      setDownloadedNexusMods(await modsApi.getDownloadedNexusMods());
    } catch {
      setDownloadedNexusMods([]);
    } finally {
      setNexusInventoryLoading(false);
    }
  }, []);

  React.useEffect(() => {
    modsApi.getMods().then((m) => {
      setMods(m);
      setLoading(false);
    });
    modsApi.getModsPath().then(setModsPathInfo);
    modsApi.getWishlist().then(setWishlist).catch(() => setWishlist([]));
    void refreshWorkshopCache(false);
    void refreshDownloadedNexusMods();
    serverSettingsApi
      .getSettings()
      .then(({ fields }) => {
        const field = fields.find((f) => f.key === "bAllowClientMod");
        setAllowMods(field ? Boolean(field.value) : null);
      })
      .catch(() => setAllowMods(null));
  }, [refreshDownloadedNexusMods, refreshWorkshopCache]);

  React.useEffect(() => {
    if (user.role !== "super_admin") return;
    const timer = window.setInterval(() => {
      void refreshWorkshopCache(true);
    }, 5000);
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        void refreshWorkshopCache(true);
        void refreshDownloadedNexusMods();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refreshDownloadedNexusMods, refreshWorkshopCache, user.role]);

async function handleUninstallDownloadedNexusMod() {
    if (!nexusUninstallTarget) return;
    setNexusInventoryBusyId(nexusUninstallTarget.id);
    try {
      const inventory = await modsApi.uninstallDownloadedNexusMod(nexusUninstallTarget.id);
      setDownloadedNexusMods(inventory);
      setMods(await modsApi.getMods());
      notifications.warning({
        title: t("mods.nexusDownloaded.uninstalledTitle", { defaultValue: "Nexus mod uninstalled" }),
        message: t("mods.nexusDownloaded.uninstalledMessage", {
          defaultValue: "{{name}} was removed from the selected server.",
          name: nexusUninstallTarget.name,
        }),
      });
    } catch (error) {
      notifications.error({
        title: t("mods.nexusDownloaded.uninstallFailedTitle", { defaultValue: "Nexus uninstall failed" }),
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setNexusInventoryBusyId(null);
      setNexusUninstallTarget(null);
    }
  }

  async function handleInstallCached(item: WorkshopCacheItem) {
    setCacheBusyId(item.workshopId);
    try {
      const updated = await modsApi.installWorkshopFromCache(item.workshopId);
      setMods(updated);
      await refreshWorkshopCache(false);
      notifications.success({
        title: item.status === "update_available"
          ? t("mods.cache.updatedTitle", { defaultValue: "Workshop mod updated" })
          : t("mods.cache.installedTitle", { defaultValue: "Workshop mod installed" }),
        message: t("mods.cache.installedMessage", { defaultValue: "{{name}} was installed for the selected server.", name: item.name }),
      });
    } catch (error) {
      notifications.error({
        title: t("mods.cache.installFailedTitle", { defaultValue: "Workshop installation failed" }),
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setCacheBusyId(null);
    }
  }

  // Synchronized with Server Settings' "Allow Client Mods" field - both read
  // and write the same bAllowClientMod ini value through the same endpoint,
  // so toggling here or there stays in sync with no separate storage.
  async function handleToggleAllowMods(checked: boolean) {
    setSavingAllowMods(true);
    try {
      await serverSettingsApi.updateSettings({ bAllowClientMod: checked });
      setAllowMods(checked);
      if (checked) {
        completeQuestStep("mods_choice");
      }
    } finally {
      setSavingAllowMods(false);
    }
  }

  async function handleReorder(next: Mod[]) {
    const withPriority = next.map((m, i) => ({ ...m, loadPriority: i + 1 }));
    setMods(withPriority);
    await modsApi.reorderMods(withPriority.map((m) => m.id));
    completeQuestStep("reorder");
  }

  async function handleToggle(mod: Mod, next: boolean) {
    setBusyId(mod.id);
    try {
      const updated = next ? await modsApi.enableMod(mod.id) : await modsApi.disableMod(mod.id);
      setMods(updated);
      if (updated.length > 0 && updated.every((m) => m.status !== "enabled")) {
        completeQuestStep("disable_all");
      }
      notifications.success({
        title: next
          ? t("mods.notifications.enabledTitle", { defaultValue: "Mod enabled" })
          : t("mods.notifications.disabledTitle", { defaultValue: "Mod disabled" }),
        message: next
          ? t("mods.notifications.enabledMessage", { defaultValue: "{{name}} runes are now glowing.", name: mod.name })
          : t("mods.notifications.disabledMessage", {
              defaultValue: "{{name}} runes are now dormant.",
              name: mod.name,
            }),
      });
    } finally {
      setBusyId(null);
    }
  }

  async function handleRequestUpdate(mod: Mod) {
    setBusyId(mod.id);
    try {
      if (mod.workshopId) {
        setMods(await modsApi.updateWorkshopMod(mod.workshopId));
        notifications.success({ title: "Workshop mod updated", message: `${mod.name} was updated successfully.` });
      } else if (mod.sourceModId) {
        const updated = await modsApi.requestModUpdate(mod);
        setWishlist(updated);
        notifications.success({
          title: "Nexus update requested",
          message: `${mod.name}'s update is waiting for super-admin approval.`,
        });
      }
    } finally {
      setBusyId(null);
    }
  }

  async function handleUpdateAll() {
    setUpdatingAll(true);
    try {
      const result = await modsApi.updateAllWorkshopMods();
      setMods(result.mods);
      setUpdateAllOpen(false);
      if (result.updated > 0) {
        notifications.success({
          title: "Workshop mods updated",
          message: `${result.updated} mod(s) updated. Pal/Saved and Mods were backed up. Manual server restart required.`,
        });
      } else {
        notifications.success({
          title: "MODS ARE UP TO DATE",
          message: "No Workshop mod updates were available.",
        });
      }
    } catch (e) {
      notifications.error({
        title: "Could not update Workshop mods",
        message: e instanceof Error ? e.message : "Unknown error.",
      });
    } finally {
      setUpdatingAll(false);
    }
  }

  async function handleRemove() {
    if (!removeTarget) return;
    setBusyId(removeTarget.id);
    try {
      const updated = await modsApi.removeMod(removeTarget.id);
      setMods(updated);
      await refreshDownloadedNexusMods();
      notifications.warning({
        title: t("mods.notifications.removedTitle", { defaultValue: "Mod removed" }),
        message: t("mods.notifications.removedMessage", {
          defaultValue: "{{name}} has been struck from the archive.",
          name: removeTarget.name,
        }),
      });
    } finally {
      setBusyId(null);
      setRemoveTarget(null);
    }
  }

  const workshopMods = mods.filter((m) => Boolean(m.workshopId));
  const nexusMods = mods.filter((m) => !m.workshopId);
  const enabledCount = workshopMods.filter((m) => m.status === "enabled").length;
  const brokenCount = workshopMods.filter((m) => m.status === "broken").length;
  const pendingNexusRequests = wishlist.filter((r) => (r.source ?? "nexus") !== "steam" && !nexusMods.some((m) => m.sourceModId === r.nexusModId));
  const pendingSteamRequests = wishlist.filter((r) => r.source === "steam");

  return (
    <div className="space-y-6">
      <Panel
        icon={<BookOpen />}
        title={t("mods.title", { defaultValue: "Mods" })}
        actions={
          <div className="flex items-center gap-2">
            <ActionButton
              variant="gold"
              size="sm"
              icon={<RefreshCw />}
              onClick={() => setUpdateAllOpen(true)}
              disabled={!mods.some((mod) => mod.updateAvailable)}
            >
              Update All Mods
            </ActionButton>
          </div>
        }
      >
        {modsPathInfo && !modsPathInfo.modsPath && (
          <div className="mb-5 flex flex-wrap items-center gap-2 rounded-md border border-life-600/30 bg-life-500/5 px-4 py-3 text-xs text-life-300">
            <TriangleAlert className="h-4 w-4 shrink-0" />
            <span>
              {t("mods.noModsPathBanner", {
                defaultValue:
                  "No Mods folder is configured yet, so verified file installs need Super Admin setup first.",
              })}
            </span>
            {user.role === "super_admin" ? (
              <Link
                to="/super-admin"
                className="ml-auto font-semibold underline decoration-dotted underline-offset-2 hover:text-life-200"
              >
                {t("mods.noModsPathCta", { defaultValue: "Set it up in Super Admin" })}
              </Link>
            ) : (
              <span className="ml-auto text-life-300/70">
                {t("mods.noModsPathAskAdmin", { defaultValue: "Ask the super admin to set it up." })}
              </span>
            )}
          </div>
        )}

        {allowMods !== null && (
          <QuestSpotlight stepId="mods_choice" className="mb-5">
            <EgmToggle
              id="allow-mods"
              checked={allowMods}
              disabled={savingAllowMods}
              onCheckedChange={handleToggleAllowMods}
              label={t("mods.allowMods", { defaultValue: "Allow Mods" })}
              description={t("mods.allowModsDescription", {
                defaultValue:
                  "Lets players with client mods enabled join. Synced with Server Settings' Allow Client Mods field.",
              })}
            />
          </QuestSpotlight>
        )}

        <div className="mb-5 flex flex-wrap items-center gap-4 text-xs text-parchment-300/60">
          <span>
            <span className="font-mono text-life-400">{enabledCount}</span>{" "}
            {t("mods.status.enabled", { defaultValue: "enabled" })}
          </span>
          <span>
            <span className="font-mono text-parchment-300/50">{workshopMods.length - enabledCount - brokenCount}</span>{" "}
            {t("mods.status.disabled", { defaultValue: "disabled" })}
          </span>
          {brokenCount > 0 && (
            <span>
              <span className="font-mono text-blood-400">{brokenCount}</span>{" "}
              {t("mods.status.broken", { defaultValue: "broken" })}
            </span>
          )}
          <span className="ml-auto text-parchment-300/40">
            {t("mods.dragHint", { defaultValue: "Drag the handle to change load priority" })}
          </span>
        </div>

        {loading ? (
          <div className="flex h-40 items-center justify-center text-parchment-300/50">
            <p className="animate-pulse font-display">
              {t("mods.loading", { defaultValue: "Unsealing the grimoire..." })}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <QuestSpotlight stepId={["reorder", "disable_all"]}>
              <Reorder.Group axis="y" values={workshopMods} onReorder={handleReorder} className="space-y-4">
                {workshopMods.map((mod) => (
                  <ModCard
                    key={mod.id}
                    mod={mod}
                    onToggle={handleToggle}
                    onRemove={setRemoveTarget}
                    onRequestUpdate={handleRequestUpdate}
                    updateRequested={false}
                    busy={busyId === mod.id}
                  />
                ))}
              </Reorder.Group>
            </QuestSpotlight>
          </div>
        )}
      </Panel>

      {user.role === "super_admin" && (
        <Panel
          icon={<HardDrive />}
          title={t("mods.cache.title", { defaultValue: "Downloaded Workshop Mods" })}
          actions={
            <ActionButton
              variant="mana"
              size="sm"
              icon={<RefreshCw className={cacheLoading ? "animate-spin" : ""} />}
              onClick={() => void refreshWorkshopCache(false)}
              disabled={cacheLoading}
            >
              {t("mods.cache.rescan", { defaultValue: "Rescan Workshop Cache" })}
            </ActionButton>
          }
        >
          <p className="mb-5 text-sm leading-relaxed text-parchment-300/65">
            {t("mods.cache.description", {
              defaultValue: "Mods downloaded through the external SteamCMD console appear here automatically. Install or update them for the currently selected server with one click.",
            })}
          </p>
          {workshopCache.length === 0 ? (
            <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-8 text-center text-sm text-parchment-300/45">
              {t("mods.cache.empty", { defaultValue: "No downloaded Palworld Workshop mods were detected." })}
            </div>
          ) : (
            <div className="space-y-3">
              {workshopCache.map((item) => {
                const canInstall = item.status === "ready" || item.status === "update_available";
                const statusLabel = item.status === "ready"
                  ? t("mods.cache.ready", { defaultValue: "Ready to install" })
                  : item.status === "update_available"
                    ? t("mods.cache.updateAvailable", { defaultValue: "Update available" })
                    : item.status === "installed"
                      ? t("mods.cache.installed", { defaultValue: "Installed" })
                      : t("mods.cache.invalid", { defaultValue: "Invalid" });
                return (
                  <div key={item.workshopId} className="flex flex-col gap-4 rounded-lg border border-stone-700/70 bg-stone-950/35 p-4 lg:flex-row lg:items-center">
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      {item.previewUrl ? (
                        <img src={item.previewUrl} alt="" className="h-16 w-16 rounded-md border border-stone-700 object-cover" />
                      ) : (
                        <div className="flex h-16 w-16 items-center justify-center rounded-md border border-stone-700 bg-stone-900/70"><Download className="h-6 w-6 text-mana-300" /></div>
                      )}
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-parchment-100">{item.name}</p>
                        <p className="text-xs text-parchment-300/55">{item.author} · ID {item.workshopId}</p>
                        <p className="mt-1 text-xs text-parchment-300/45">{item.packageName || item.validationError}</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between gap-3 lg:justify-end">
                      <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${item.status === "invalid" ? "border-blood-500/40 text-blood-300" : item.status === "installed" ? "border-life-500/40 text-life-300" : "border-mana-500/40 text-mana-300"}`}>
                        {item.status === "invalid" ? <CircleAlert className="h-3.5 w-3.5" /> : item.status === "installed" ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Download className="h-3.5 w-3.5" />}
                        {statusLabel}
                      </span>
                      {canInstall && (
                        <ActionButton
                          variant="mana"
                          size="sm"
                          onClick={() => void handleInstallCached(item)}
                          disabled={cacheBusyId === item.workshopId}
                        >
                          {cacheBusyId === item.workshopId
                            ? t("common.working", { defaultValue: "Working..." })
                            : item.status === "update_available"
                              ? t("mods.cache.update", { defaultValue: "Update" })
                              : t("mods.cache.install", { defaultValue: "Install" })}
                        </ActionButton>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>
      )}

      <Ue4ssPanel />

      <Panel
        icon={<ScrollText />}
        title={t("mods.steamWishlist.title", { defaultValue: "Steam Workshop Wishlist" })}
        actions={
          <ActionButton variant="mana" size="sm" icon={<ScrollText />} onClick={() => setBrowseOpen(true)}>
            {t("mods.browseWorkshop", { defaultValue: "Browse Steam Workshop" })}
          </ActionButton>
        }
      >
        <p className="mb-5 text-sm leading-relaxed text-parchment-300/65">
          {t("mods.steamWishlist.description", { defaultValue: "Steam Workshop requests are managed separately from Nexus Mods. The super admin downloads approved items through SteamCMD and installs them for the selected server." })}
        </p>
        {pendingSteamRequests.length === 0 ? (
          <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-8 text-center text-sm text-parchment-300/45">
            {t("mods.steamWishlist.empty", { defaultValue: "No Steam Workshop mods are waiting for approval." })}
          </div>
        ) : (
          <div className="space-y-4">
            {pendingSteamRequests.map((request) => <PendingModCard key={request.id} request={request} />)}
          </div>
        )}
      </Panel>

<Panel
        icon={<HardDrive />}
        title={t("mods.nexusDownloaded.title", { defaultValue: "Downloaded Nexus Mods" })}
        actions={
          <ActionButton
            variant="mana"
            size="sm"
            icon={<RefreshCw className={nexusInventoryLoading ? "animate-spin" : ""} />}
            onClick={() => void refreshDownloadedNexusMods()}
            disabled={nexusInventoryLoading}
          >
            {t("mods.nexusDownloaded.rescan", { defaultValue: "Rescan Nexus Mods" })}
          </ActionButton>
        }
      >
        <p className="mb-5 text-sm leading-relaxed text-parchment-300/65">
          {t("mods.nexusDownloaded.description", {
            defaultValue: "Approved Nexus Mods downloaded and installed for the currently selected server are listed here. Uninstall removes the installed files, downloaded archive and saved server entry.",
          })}
        </p>

        {downloadedNexusMods.length === 0 ? (
          <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-8 text-center text-sm text-parchment-300/45">
            {t("mods.nexusDownloaded.empty", { defaultValue: "No downloaded Nexus Mods were detected for this server." })}
          </div>
        ) : (
          <div className="space-y-3">
            {downloadedNexusMods.map((item) => {
              const statusLabel =
                item.status === "installed"
                  ? t("mods.nexusDownloaded.installed", { defaultValue: "Installed" })
                  : item.status === "configured"
                    ? t("mods.nexusDownloaded.configured", { defaultValue: "Configured — restart required" })
                    : item.status === "downloaded"
                      ? t("mods.nexusDownloaded.downloaded", { defaultValue: "Downloaded" })
                      : t("mods.nexusDownloaded.missing", { defaultValue: "Files missing" });

              return (
                <div
                  key={item.id}
                  className="flex flex-col gap-4 rounded-lg border border-stone-700/70 bg-stone-950/35 p-4 lg:flex-row lg:items-center"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    {item.previewUrl ? (
                      <img
                        src={item.previewUrl}
                        alt=""
                        className="h-16 w-16 rounded-md border border-stone-700 object-cover"
                      />
                    ) : (
                      <div className="flex h-16 w-16 items-center justify-center rounded-md border border-stone-700 bg-stone-900/70">
                        <Download className="h-6 w-6 text-life-300" />
                      </div>
                    )}

                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate font-semibold text-parchment-100">{item.name}</p>
                        {item.nexusUrl && (
                          <a
                            href={item.nexusUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-life-300 transition hover:text-life-200"
                            title={t("mods.nexusDownloaded.openNexus", { defaultValue: "Open on Nexus Mods" })}
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        )}
                      </div>
                      <p className="text-xs text-parchment-300/55">
                        {item.author} · Nexus ID {item.modId || "—"} · v{item.version}
                      </p>
                      <p className="mt-1 truncate text-xs text-parchment-300/45">
                        {item.packageName || item.folderName || item.installedPath || item.downloadedFile || item.installKind}
                      </p>
                      <p className="mt-1 text-[11px] text-parchment-300/40">
                        {item.installMode}
                        {item.installKind === "ue4ss" ? " — UE4SS Mods directory" : ""}
                        {item.deploymentMessage ? ` — ${item.deploymentMessage}` : ""}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 lg:justify-end">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${
                        item.status === "installed"
                          ? "border-life-500/40 text-life-300"
                          : item.status === "configured"
                            ? "border-gold-500/40 text-gold-300"
                            : item.status === "downloaded"
                              ? "border-mana-500/40 text-mana-300"
                              : "border-blood-500/40 text-blood-300"
                      }`}
                    >
                      {item.status === "installed" ? (
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      ) : item.status === "configured" ? (
                        <RefreshCw className="h-3.5 w-3.5" />
                      ) : item.status === "downloaded" ? (
                        <Download className="h-3.5 w-3.5" />
                      ) : (
                        <CircleAlert className="h-3.5 w-3.5" />
                      )}
                      {statusLabel}
                    </span>

                    {item.runtimeVerification && (
                      <span
                        className={`inline-flex max-w-[360px] items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs ${
                          item.runtimeVerification.state === "verified"
                            ? "border-life-500/40 text-life-300"
                            : item.runtimeVerification.state === "warning"
                              ? "border-gold-500/40 text-gold-300"
                              : "border-blood-500/40 text-blood-300"
                        }`}
                        title={`${item.runtimeVerification.evidence} Confidence: ${item.runtimeVerification.confidence}`}
                      >
                        {item.runtimeVerification.state === "verified"
                          ? t("mods.runtime.verified", { defaultValue: "Runtime verified" })
                          : item.runtimeVerification.state === "warning"
                            ? t("mods.runtime.warning", { defaultValue: "Runtime unconfirmed" })
                            : t("mods.runtime.failed", { defaultValue: "Runtime failed" })}
                      </span>
                    )}

                    <ActionButton
                      variant="danger"
                      size="sm"
                      icon={<Trash2 />}
                      onClick={() => setNexusUninstallTarget(item)}
                      disabled={nexusInventoryBusyId === item.id}
                    >
                      {nexusInventoryBusyId === item.id
                        ? t("common.working", { defaultValue: "Working..." })
                        : t("mods.nexusDownloaded.uninstall", { defaultValue: "Uninstall" })}
                    </ActionButton>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Panel>

      <Panel
        icon={<Boxes />}
        title={t("mods.nexusWishlist.title", { defaultValue: "Nexus Mods Wishlist" })}
        actions={
          <ActionButton variant="mana" size="sm" icon={<ScrollText />} onClick={() => setNexusBrowseOpen(true)}>
            {t("mods.nexusWishlist.browse", { defaultValue: "Browse Nexus Mods" })}
          </ActionButton>
        }
      >
        <p className="mb-5 text-sm leading-relaxed text-parchment-300/65">
          {t("mods.nexusWishlist.description", {
            defaultValue: "Nexus Mods requests waiting for approval are listed here. Approved and installed mods appear separately under Downloaded Nexus Mods.",
          })}
        </p>
        {pendingNexusRequests.length === 0 ? (
          <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-8 text-center text-sm text-parchment-300/45">
            {t("mods.nexusWishlist.empty", { defaultValue: "No Nexus Mods are waiting for approval." })}
          </div>
        ) : (
          <div className="space-y-4">
            {pendingNexusRequests.map((request) => (
              <PendingModCard key={request.id} request={request} />
            ))}
          </div>
        )}
      </Panel>

<Modal
        open={!!nexusUninstallTarget}
        onOpenChange={(open) => !open && setNexusUninstallTarget(null)}
        tone="danger"
        title={t("mods.nexusDownloaded.uninstallDialogTitle", { defaultValue: "Uninstall this Nexus mod?" })}
        description={t("mods.nexusDownloaded.uninstallDialogDescription", {
          defaultValue: "{{name}} will be removed from the selected server, including its installed files and downloaded archive.",
          name: nexusUninstallTarget?.name,
        })}
        confirmLabel={t("mods.nexusDownloaded.uninstall", { defaultValue: "Uninstall" })}
        onConfirm={handleUninstallDownloadedNexusMod}
        confirming={nexusInventoryBusyId === nexusUninstallTarget?.id}
      />

      <Modal
        open={!!removeTarget}
        onOpenChange={(o) => !o && setRemoveTarget(null)}
        tone="danger"
        title={t("mods.removeDialog.title", { defaultValue: "Remove this mod?" })}
        description={t("mods.removeDialog.description", {
          defaultValue: "{{name}} will be permanently removed from your server's load order.",
          name: removeTarget?.name,
        })}
        confirmLabel={t("mods.removeDialog.confirm", { defaultValue: "Remove" })}
        onConfirm={handleRemove}
        confirming={busyId === removeTarget?.id}
      />

      <Modal
        open={updateAllOpen}
        onOpenChange={setUpdateAllOpen}
        title="Update all Workshop mods?"
        description="Only mods with available updates will be updated. Before the update, ExilesGameManager backs up Pal/Saved and Mods. The server will not be started, stopped, or restarted."
        confirmLabel="Update All Mods"
        onConfirm={handleUpdateAll}
        confirming={updatingAll}
      />

      <WorkshopInstallDialog open={browseOpen} onOpenChange={setBrowseOpen} onInstalled={setMods} />
      <NexusBrowseDialog open={nexusBrowseOpen} onOpenChange={setNexusBrowseOpen} installedNames={nexusMods.map((m) => m.name)} />
    </div>
  );
}

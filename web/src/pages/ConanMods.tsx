import * as React from "react";
import { Reorder } from "framer-motion";
import { BookOpen, Download, RefreshCw, Trash2, ScrollText, HardDrive } from "lucide-react";
import { modsApi } from "@/api";
import type { Mod, WorkshopDetails } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";
import { Modal } from "@/components/ui/modal";
import { ModCard } from "@/components/mods/ModCard";
import { useNotifications } from "@/hooks/useNotifications";
import { WorkshopInstallDialog } from "@/components/mods/WorkshopInstallDialog";

export default function ConanMods() {
  const notifications = useNotifications();
  const [mods, setMods] = React.useState<Mod[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [busyId, setBusyId] = React.useState<string | null>(null);
  const [workshopValue, setWorkshopValue] = React.useState("");
  const [details, setDetails] = React.useState<WorkshopDetails | null>(null);
  const [installing, setInstalling] = React.useState(false);
  const [checking, setChecking] = React.useState(false);
  const [updatingAll, setUpdatingAll] = React.useState(false);
  const [removeTarget, setRemoveTarget] = React.useState<Mod | null>(null);
  const [browseOpen, setBrowseOpen] = React.useState(false);
  const [workshopCache, setWorkshopCache] = React.useState<any[]>([]);
  const [cacheLoading, setCacheLoading] = React.useState(false);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    try {
      setMods(await modsApi.getMods());
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshCache = React.useCallback(async () => {
    setCacheLoading(true);
    try {
      setWorkshopCache(await modsApi.getWorkshopCache());
    } finally {
      setCacheLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
    void refreshCache();
  }, [refresh, refreshCache]);

  async function inspectWorkshop() {
    const value = workshopValue.trim();
    if (!value) return;
    setInstalling(true);
    try {
      const next = await modsApi.getWorkshopDetails(value);
      setDetails(next);
    } catch (error) {
      setDetails(null);
      notifications.error({
        title: "Conan Workshop item could not be loaded",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setInstalling(false);
    }
  }

  async function installWorkshop() {
    const value = details?.workshopId || workshopValue.trim();
    if (!value) return;
    setInstalling(true);
    try {
      const next = await modsApi.installWorkshopMod(value);
      setMods(next);
      setWorkshopValue("");
      setDetails(null);
      notifications.success({
        title: "Conan Workshop mod installed",
        message: "The mod remains in the SteamCMD Workshop cache and its .pak path was added to ConanSandbox/Mods/modlist.txt. Restart Conan to apply it.",
      });
    } catch (error) {
      notifications.error({
        title: "Conan Workshop installation failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setInstalling(false);
    }
  }

  async function handleToggle(mod: Mod, enabled: boolean) {
    setBusyId(mod.id);
    try {
      setMods(enabled ? await modsApi.enableMod(mod.id) : await modsApi.disableMod(mod.id));
      notifications.success({
        title: enabled ? "Conan mod enabled" : "Conan mod disabled",
        message: `${mod.name}: modlist.txt was updated. Restart Conan to apply the change.`,
      });
    } catch (error) {
      notifications.error({
        title: "Conan mod change failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setBusyId(null);
    }
  }

  async function handleReorder(next: Mod[]) {
    const ordered = next.map((mod, index) => ({ ...mod, loadPriority: index + 1 }));
    setMods(ordered);
    try {
      setMods(await modsApi.reorderMods(ordered.map((mod) => mod.id)));
    } catch (error) {
      await refresh();
      notifications.error({
        title: "Conan load order update failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    }
  }

  async function handleUpdate(mod: Mod) {
    if (!mod.workshopId) return;
    setBusyId(mod.id);
    try {
      setMods(await modsApi.updateWorkshopMod(mod.workshopId));
      notifications.success({
        title: "Conan Workshop mod updated",
        message: `${mod.name} was updated. Restart Conan to load the new files.`,
      });
    } catch (error) {
      notifications.error({
        title: "Conan Workshop update failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setBusyId(null);
    }
  }

  async function checkUpdates() {
    setChecking(true);
    try {
      const result = await modsApi.checkWorkshopUpdates();
      setMods(result.mods || (await modsApi.getMods()));
      notifications.success({
        title: "Conan Workshop check complete",
        message: `${result.updatesAvailable} update(s) available.`,
      });
    } catch (error) {
      notifications.error({
        title: "Conan Workshop check failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setChecking(false);
    }
  }

  async function updateAll() {
    setUpdatingAll(true);
    try {
      const result = await modsApi.updateAllWorkshopMods();
      setMods(result.mods);
      notifications.success({
        title: "Conan Workshop updates complete",
        message: result.updated > 0
          ? `${result.updated} mod(s) updated. Restart Conan to apply them.`
          : "All Conan Workshop mods are already up to date.",
      });
    } catch (error) {
      notifications.error({
        title: "Conan Workshop update failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setUpdatingAll(false);
    }
  }

  async function removeMod() {
    if (!removeTarget) return;
    setBusyId(removeTarget.id);
    try {
      setMods(await modsApi.removeMod(removeTarget.id));
      notifications.warning({
        title: "Conan Workshop mod removed",
        message: `${removeTarget.name} was removed from modlist.txt. The SteamCMD Workshop cache is retained.`,
      });
    } catch (error) {
      notifications.error({
        title: "Conan Workshop removal failed",
        message: error instanceof Error ? error.message : "Unknown error.",
      });
    } finally {
      setBusyId(null);
      setRemoveTarget(null);
    }
  }

  const updatesAvailable = mods.filter((mod) => mod.updateAvailable).length;
  const enabled = mods.filter((mod) => mod.status === "enabled").length;

  return (
    <div className="space-y-6">
      <Panel
        icon={<BookOpen />}
        title="Conan Exiles Mods — Steam Workshop"
        actions={
          <div className="flex flex-wrap gap-2">
            <ActionButton variant="mana" size="sm" icon={<ScrollText />} onClick={() => setBrowseOpen(true)}>
              Browse Workshop
            </ActionButton>
            <ActionButton variant="mana" size="sm" icon={<RefreshCw className={checking ? "animate-spin" : ""} />} onClick={() => void checkUpdates()} disabled={checking}>
              Check Updates
            </ActionButton>
            <ActionButton variant="gold" size="sm" icon={<Download />} onClick={() => void updateAll()} disabled={updatingAll || updatesAvailable === 0}>
              Update All
            </ActionButton>
          </div>
        }
      >
        <div className="mb-5 rounded-lg border border-mana-500/20 bg-mana-500/[0.05] p-4 text-sm text-parchment-300/70">
          Conan Exiles uses its own Steam Workshop catalog. EGM downloads Workshop items through SteamCMD anonymously into the selected Conan server library under &lt;ServerPath&gt;/steamapps/workshop/content/440900/&lt;WorkshopID&gt;. ConanSandbox/Mods/modlist.txt references the absolute .pak paths from that server-local cache in the load order shown below. Nexus Mods and UE4SS are intentionally not used for Conan.
        </div>

        <div className="mb-5 grid gap-3 lg:grid-cols-[1fr_auto_auto]">
          <input
            value={workshopValue}
            onChange={(event) => {
              setWorkshopValue(event.target.value);
              setDetails(null);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter") void inspectWorkshop();
            }}
            placeholder="Steam Workshop URL or Workshop ID"
            className="min-w-0 rounded-md border border-parchment-500/20 bg-black/30 px-3 py-2 font-mono text-sm text-parchment-100 outline-none focus:border-mana-400/60"
          />
          <ActionButton variant="ghost" onClick={() => void inspectWorkshop()} disabled={!workshopValue.trim() || installing}>
            Verify
          </ActionButton>
          <ActionButton variant="mana" icon={<Download />} onClick={() => void installWorkshop()} disabled={!workshopValue.trim() || installing}>
            {installing ? "Working..." : "Install"}
          </ActionButton>
        </div>

        {details && (
          <div className="mb-5 flex gap-4 rounded-lg border border-stone-700/70 bg-stone-950/35 p-4">
            {details.previewUrl && <img src={details.previewUrl} alt="" className="h-20 w-20 rounded-md border border-stone-700 object-cover" />}
            <div className="min-w-0">
              <p className="font-semibold text-parchment-100">{details.title}</p>
              <p className="mt-1 text-xs text-parchment-300/55">Workshop ID {details.workshopId} · {details.owner}</p>
              {details.description && <p className="mt-2 line-clamp-3 text-xs leading-relaxed text-parchment-300/55">{details.description}</p>}
            </div>
          </div>
        )}

        <div className="mb-4 flex flex-wrap gap-4 text-xs text-parchment-300/60">
          <span><span className="font-mono text-life-400">{enabled}</span> enabled</span>
          <span><span className="font-mono text-parchment-300/60">{mods.length - enabled}</span> disabled</span>
          <span><span className="font-mono text-gold-300">{updatesAvailable}</span> update(s)</span>
          <span className="ml-auto">Drag cards to change Conan mod load order.</span>
        </div>

        {loading ? (
          <div className="flex h-36 items-center justify-center text-sm text-parchment-300/50">Loading Conan Workshop mods...</div>
        ) : mods.length === 0 ? (
          <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-10 text-center text-sm text-parchment-300/45">
            No Conan Workshop mods are installed for this server.
          </div>
        ) : (
          <Reorder.Group axis="y" values={mods} onReorder={handleReorder} className="space-y-4">
            {mods.map((mod) => (
              <ModCard
                key={mod.id}
                mod={mod}
                onToggle={handleToggle}
                onRemove={setRemoveTarget}
                onRequestUpdate={handleUpdate}
                updateRequested={false}
                busy={busyId === mod.id}
                context="conan"
              />
            ))}
          </Reorder.Group>
        )}
      </Panel>

      <Panel
        icon={<HardDrive />}
        title="Downloaded Conan Workshop Mods"
        actions={<ActionButton variant="mana" size="sm" icon={<RefreshCw className={cacheLoading ? "animate-spin" : ""} />} onClick={() => void refreshCache()} disabled={cacheLoading}>Rescan Workshop Cache</ActionButton>}
      >
        {workshopCache.length === 0 ? (
          <div className="rounded-md border border-stone-700/70 bg-stone-900/25 px-4 py-8 text-center text-sm text-parchment-300/45">No Conan Workshop mods are currently downloaded in SteamCMD.</div>
        ) : (
          <div className="space-y-3">
            {workshopCache.map((item:any) => (
              <div key={item.workshopId} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-stone-700/70 bg-stone-950/35 p-4">
                <div className="min-w-0">
                  <p className="font-semibold text-parchment-100">{item.name || `Workshop ${item.workshopId}`}</p>
                  <p className="mt-1 break-all font-mono text-[11px] text-parchment-300/45">{item.path}</p>
                </div>
                <ActionButton variant="ghost" size="sm" onClick={() => { setWorkshopValue(String(item.workshopId)); setDetails(null); }}>Use ID {item.workshopId}</ActionButton>
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel icon={<Trash2 />} title="Conan Mod Runtime">
        <p className="text-sm leading-relaxed text-parchment-300/65">
          Mod file changes are prepared while EGM is running, but Conan loads modlist.txt when the dedicated server starts. Restart the server after install, update, enable, disable, remove, or load-order changes.
        </p>
      </Panel>

      <Modal
        open={Boolean(removeTarget)}
        onOpenChange={(open) => !open && setRemoveTarget(null)}
        tone="danger"
        title="Remove this Conan Workshop mod?"
        description={`${removeTarget?.name || "This mod"} will be removed from the Conan modlist. The downloaded SteamCMD Workshop cache is retained.`}
        confirmLabel="Remove Mod"
        onConfirm={removeMod}
        confirming={busyId === removeTarget?.id}
      />

      <WorkshopInstallDialog open={browseOpen} onOpenChange={setBrowseOpen} onInstalled={(next) => { setMods(next); void refreshCache(); }} mode="install" />
    </div>
  );
}

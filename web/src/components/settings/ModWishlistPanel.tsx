import * as React from "react";
import { Check, ExternalLink, Heart, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { modsApi } from "@/api";
import type { Mod, ModWishlistRequest } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";
import { useNotifications } from "@/hooks/useNotifications";
import { useActiveQuestStep } from "@/hooks/useActiveQuestStep";
import { completeQuestStep } from "@/lib/questCompletion";

export function ModWishlistPanel() {
  const { t } = useTranslation();
  const notifications = useNotifications();
  const { nextStep } = useActiveQuestStep();
  const [requests, setRequests] = React.useState<ModWishlistRequest[]>([]);
  const [installedMods, setInstalledMods] = React.useState<Mod[]>([]);
  const [busyId, setBusyId] = React.useState<string | null>(null);
  // Session-scoped: how many approvals have happened while approve_one is
  // the active Mod Supervisor step, since a wishlist request is removed
  // once decided and can't be counted after the fact from persisted state.
  const approvedDuringQuest = React.useRef(0);

  React.useEffect(() => {
    modsApi.getWishlist().then(setRequests);
    modsApi.getMods().then(setInstalledMods);
  }, []);

  async function decide(request: ModWishlistRequest, approve: boolean) {
    setBusyId(request.id);
    try {
      const updated = approve
        ? await modsApi.approveWishlistRequest(request.id)
        : await modsApi.denyWishlistRequest(request.id);
      setRequests(updated);
      if (approve && nextStep?.id === "approve_one") {
        approvedDuringQuest.current += 1;
        if (approvedDuringQuest.current >= 2) {
          completeQuestStep("approve_one");
        }
      }
      notifications.success({
        title: approve
          ? t("superAdmin.modWishlist.approvedTitle", { defaultValue: "Mod approved and installed" })
          : t("superAdmin.modWishlist.deniedTitle", { defaultValue: "Mod request denied" }),
        message: request.name,
      });
    } catch (error) {
      notifications.error({
        title: t("superAdmin.modWishlist.actionFailed", { defaultValue: "Could not process request" }),
        message: error instanceof Error ? error.message : t("common.unknownError", { defaultValue: "Unknown error." }),
      });
    } finally {
      setBusyId(null);
    }
  }

  const nexusRequests = requests.filter((request) => (request.source ?? "nexus") !== "steam");
  const steamRequests = requests.filter((request) => request.source === "steam");

  function renderRequests(items: ModWishlistRequest[], source: "nexus" | "steam") {
    if (items.length === 0) {
      return (
        <p className="rounded-md border border-stone-700 bg-abyss-950/30 px-4 py-8 text-center text-sm text-parchment-300/45">
          {source === "steam"
            ? t("superAdmin.modWishlist.emptySteam", { defaultValue: "No Steam Workshop requests are waiting." })
            : t("superAdmin.modWishlist.emptyNexus", { defaultValue: "No Nexus Mods requests are waiting." })}
        </p>
      );
    }
    return (
      <div className="space-y-3">
        {items.map((request) => (
          <div key={request.id} className="flex flex-col gap-3 rounded-md border border-stone-700 bg-abyss-950/35 p-4 md:flex-row md:items-center">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h4 className="truncate font-display text-sm font-semibold text-parchment-100">{request.name}</h4>
                {source === "nexus" && installedMods.some((m) => m.sourceModId === request.nexusModId) && (
                  <span className="shrink-0 rounded-full border border-mana-500/40 bg-mana-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-mana-300">
                    {t("superAdmin.modWishlist.updateBadge", { defaultValue: "Update" })}
                  </span>
                )}
                <a href={source === "steam" ? request.steamUrl : request.nexusUrl} target="_blank" rel="noreferrer" className="text-life-400 hover:text-life-300">
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
              <p className="mt-1 text-xs text-parchment-300/55">{t("superAdmin.modWishlist.requestedBy", { defaultValue: "Requested by {{username}}", username: request.requestedBy })}</p>
              {source === "steam" && request.workshopId && <p className="mt-1 font-mono text-[11px] text-mana-300/70">Workshop ID: {request.workshopId}</p>}
              {request.summary && <p className="mt-2 line-clamp-2 text-xs text-parchment-300/65">{request.summary}</p>}
            </div>
            <div className="flex shrink-0 gap-2">
              <ActionButton size="sm" variant="life" icon={<Check />} disabled={busyId != null} onClick={() => decide(request, true)}>
                {busyId === request.id ? t("common.working", { defaultValue: "Working..." }) : t("superAdmin.modWishlist.approve", { defaultValue: "Approve" })}
              </ActionButton>
              <ActionButton size="sm" variant="danger" icon={<X />} disabled={busyId != null} onClick={() => decide(request, false)}>
                {t("superAdmin.modWishlist.deny", { defaultValue: "Deny" })}
              </ActionButton>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Panel icon={<Heart />} title={t("superAdmin.modWishlist.nexusTitle", { defaultValue: "Mod Wishlist — Nexus Mods" })}>
        <p className="mb-4 text-xs leading-relaxed text-parchment-300/50">{t("superAdmin.modWishlist.nexusDescription", { defaultValue: "Review Nexus Mods requested by administrators." })}</p>
        {renderRequests(nexusRequests, "nexus")}
      </Panel>
      <Panel icon={<Heart />} title={t("superAdmin.modWishlist.steamTitle", { defaultValue: "Mod Wishlist — Steam Workshop" })}>
        <p className="mb-4 text-xs leading-relaxed text-parchment-300/50">{t("superAdmin.modWishlist.steamDescription", { defaultValue: "Download requested items through SteamCMD first, then approve them for the selected server." })}</p>
        {renderRequests(steamRequests, "steam")}
      </Panel>
    </div>
  );
}

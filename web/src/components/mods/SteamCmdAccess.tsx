import * as React from "react";
import { ExternalLink, KeyRound, ShieldCheck, TerminalSquare } from "lucide-react";
import { useTranslation } from "react-i18next";
import { modsApi } from "@/api";
import { ActionButton } from "@/components/ui/egm-button";
import { Panel } from "@/components/ui/panel";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface Props { open: boolean; onOpenChange: (open: boolean) => void; }

export function SteamCmdAccess({ open, onOpenChange }: Props) {
  const { t } = useTranslation();
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [opened, setOpened] = React.useState(false);

  async function openConsole() {
    setBusy(true);
    setError(null);
    try {
      await modsApi.openSteamCmdConsole();
      setOpened(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not open SteamCMD.");
    } finally {
      setBusy(false);
    }
  }

  return <>
    <Panel icon={<KeyRound />} title={t("steamCmdAuth.title", { defaultValue: "Steam Workshop Access" })}>
      <p className="mb-4 text-xs leading-relaxed text-parchment-300/50">
        {t("steamCmdAuth.consoleHint", { defaultValue: "Anonymous downloads are attempted first. Open the normal SteamCMD console when Steam requires an authenticated account. EGM never receives or stores anything typed in that console." })}
      </p>
      <div className="space-y-3 rounded-md border border-mana-500/30 bg-mana-500/5 px-4 py-3">
        <div className="flex items-center gap-3 text-xs text-mana-200/80">
          <ShieldCheck className="h-4 w-4 shrink-0" />
          {t("steamCmdAuth.securityHint", { defaultValue: "Credentials, Steam Guard codes, and commands stay inside the external SteamCMD window." })}
        </div>
        <ActionButton variant="mana" icon={<TerminalSquare />} onClick={() => onOpenChange(true)} className="w-full">
          {t("steamCmdAuth.openConsole", { defaultValue: "Open SteamCMD Console" })}
        </ActionButton>
        <p className="text-[11px] leading-relaxed text-parchment-300/40">
          {t("steamCmdAuth.superAdminHint", { defaultValue: "Download requested Workshop items here, then approve them from the Steam Workshop Wishlist." })}
        </p>
      </div>
    </Panel>
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Open the normal SteamCMD console</DialogTitle>
          <DialogDescription>
            SteamCMD opens in its own Windows console. Account name, password, Steam Guard code, and commands stay inside that console and are never sent to EGM.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 text-sm text-parchment-300/80">
          <div className="rounded-md border border-stone-700 bg-abyss-950/50 p-4 font-mono text-xs leading-6">
            <div><span className="text-mana-300">1.</span> login YOUR_ACCOUNT_NAME YOUR_PASSWORD</div>
            <div><span className="text-mana-300">2.</span> Enter the Steam Guard code when SteamCMD requests it.</div>
            <div><span className="text-mana-300">3.</span> workshop_download_item 1623730 WORKSHOP_ID validate</div>
            <div><span className="text-mana-300">4.</span> quit</div>
          </div>
          <div className="rounded-md border border-life-500/20 bg-life-500/5 p-3 text-xs leading-relaxed text-life-200/80">
            After the download succeeds, return to EGM and click Install or Update again. EGM detects the downloaded files in the shared SteamCMD Workshop cache and installs them for the selected server instance.
          </div>
          {opened && <div className="flex items-center gap-2 text-xs text-life-300"><ShieldCheck size={15} /> SteamCMD console opened.</div>}
          {error && <p className="text-xs text-blood-400">{error}</p>}
        </div>
        <DialogFooter>
          <ActionButton variant="ghost" onClick={() => onOpenChange(false)}>Close</ActionButton>
          <ActionButton variant="mana" icon={<ExternalLink />} onClick={openConsole} disabled={busy}>
            {busy ? "Opening..." : "Open SteamCMD"}
          </ActionButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </>;
}

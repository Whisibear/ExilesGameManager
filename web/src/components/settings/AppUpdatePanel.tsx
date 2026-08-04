import * as React from "react";
import { ArrowUpCircle, CheckCircle2, ExternalLink, Loader2, RefreshCw } from "lucide-react";
import { useTranslation } from "react-i18next";
import { appUpdateApi } from "@/api";
import type { AppUpdateStatus } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";

export function AppUpdatePanel() {
  const { t } = useTranslation();
  const [status, setStatus] = React.useState<AppUpdateStatus | null>(null);
  const [checking, setChecking] = React.useState(true);
  const [installing, setInstalling] = React.useState(false);
  const installPollRef = React.useRef<number | null>(null);
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
    return () => {
      if (installPollRef.current !== null) window.clearInterval(installPollRef.current);
    };
  }, [load]);

  async function install() {
    if (!status?.updateAvailable) return;

    if (!status.installerAvailable || !status.installSupported) {
      if (status.releaseUrl) window.open(status.releaseUrl, "_blank", "noopener,noreferrer");
      return;
    }

    const confirmed = window.confirm(
      t("updates.confirmInstall", {
        version: status.latestVersion,
        defaultValue: `Install EGM ${status.latestVersion} now? EGM will close automatically.`,
      }),
    );
    if (!confirmed) return;

    setInstalling(true);
    setError(null);
    try {
      await appUpdateApi.install();
      installPollRef.current = window.setInterval(async () => {
        try {
          const next = await appUpdateApi.getStatus(false);
          setStatus(next);
          if (next.installPhase === "failed") {
            setInstalling(false);
            setError(next.installError ?? next.installMessage ?? "The automatic update failed.");
            if (installPollRef.current !== null) window.clearInterval(installPollRef.current);
          }
        } catch {
          // The backend becomes unreachable when EGM closes for installation.
          // Keep the final status visible while the external updater takes over.
        }
      }, 500);
    } catch (reason) {
      setInstalling(false);
      setError(reason instanceof Error ? reason.message : String(reason));
    }
  }

  return (
    <Panel
      icon={<ArrowUpCircle />}
      title={t("updates.panelTitle", { defaultValue: "Exiles Game Manager Update" })}
    >
      <div className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-stone-700/60 bg-black/10 p-3">
            <p className="text-[11px] uppercase tracking-[.16em] text-parchment-300/45">
              {t("updates.currentVersion", { defaultValue: "Installed version" })}
            </p>
            <p className="mt-1 font-mono text-sm text-parchment-100">{status?.currentVersion ?? "—"}</p>
          </div>
          <div className="rounded-lg border border-stone-700/60 bg-black/10 p-3">
            <p className="text-[11px] uppercase tracking-[.16em] text-parchment-300/45">
              {t("updates.latestVersion", { defaultValue: "Latest release" })}
            </p>
            <p className="mt-1 font-mono text-sm text-parchment-100">{status?.latestVersion ?? "—"}</p>
          </div>
        </div>

        {status?.updateAvailable ? (
          <div className="rounded-lg border border-life-500/25 bg-life-500/[0.06] p-3 text-sm text-life-200">
            {t("updates.updateReady", {
              version: status.latestVersion,
              defaultValue: `EGM ${status.latestVersion} is ready to install from GitHub.`,
            })}
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg border border-stone-700/60 bg-black/10 p-3 text-sm text-parchment-300/65">
            <CheckCircle2 className="h-4 w-4 text-life-300" />
            {checking
              ? t("updates.checking", { defaultValue: "Checking GitHub releases…" })
              : t("updates.upToDate", { defaultValue: "This installation is up to date." })}
          </div>
        )}


        {(installing || status?.installing) && (
          <div className="space-y-2 rounded-lg border border-mana-500/25 bg-mana-500/[0.05] p-3">
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="text-parchment-200/75">
                {status?.installMessage ?? t("updates.preparingInstall", { defaultValue: "Preparing update…" })}
              </span>
              <span className="font-mono text-mana-200">{status?.installProgress ?? 0}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-black/35">
              <div
                className="h-full rounded-full bg-mana-400 transition-[width] duration-300"
                style={{ width: `${status?.installProgress ?? 0}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/[0.07] p-3 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => void load(true)} disabled={checking || installing}>
            {checking ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {t("updates.checkNow", { defaultValue: "Check now" })}
          </Button>

          {status?.updateAvailable && (
            <Button type="button" onClick={() => void install()} disabled={checking || installing}>
              {installing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUpCircle className="h-4 w-4" />}
              {installing
                ? t("updates.installing", { defaultValue: "Installing update…" })
                : t("updates.installNow", {
                    version: status.latestVersion,
                    defaultValue: `Install ${status.latestVersion}`,
                  })}
            </Button>
          )}

          {status?.releaseUrl && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => window.open(status.releaseUrl!, "_blank", "noopener,noreferrer")}
            >
              <ExternalLink className="h-4 w-4" />
              {t("updates.openRelease", { defaultValue: "Open GitHub release" })}
            </Button>
          )}
        </div>

        <p className="text-xs leading-relaxed text-parchment-300/45">
          {t("updates.panelHint", {
            defaultValue:
              "EGM downloads the signed release installer from GitHub, verifies the published SHA-256 checksum, closes itself and starts the installer in update mode. Settings, OAuth data, servers and backups are preserved.",
          })}
        </p>
      </div>
    </Panel>
  );
}

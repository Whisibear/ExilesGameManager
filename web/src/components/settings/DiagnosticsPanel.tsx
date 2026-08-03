import * as React from "react";
import { useTranslation } from "react-i18next";
import { Stethoscope, ShieldCheck, PackageOpen, Download, Bug } from "lucide-react";
import { systemSettingsApi } from "@/api";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNotifications } from "@/hooks/useNotifications";

export function DiagnosticsPanel() {
  const { t } = useTranslation();
  const [running, setRunning] = React.useState(false);
  const [report, setReport] = React.useState<string | null>(null);
  const [reportPath, setReportPath] = React.useState<string | null>(null);
  const [packageResult, setPackageResult] = React.useState<systemSettingsApi.DiagnosticPackageResult | null>(null);
  const [settings, setSettings] = React.useState<import("@/types/models").SystemSettings | null>(null);
  const notifications = useNotifications();

  React.useEffect(() => {
    systemSettingsApi.getSystemSettings().then(setSettings).catch(() => undefined);
  }, []);

  async function handleRun(forceAdmin: boolean) {
    setRunning(true);
    try {
      const result = await systemSettingsApi.runDiagnostics(forceAdmin);
      setReport(result.report);
      setReportPath(result.reportPath);
      notifications.success({
        title: t("superAdmin.diagnostics.completeTitle", { defaultValue: "Diagnostics complete" }),
        message: t("superAdmin.diagnostics.completeMessage", { defaultValue: "See the report below." }),
      });
    } catch (e) {
      notifications.error({
        title: t("superAdmin.diagnostics.failedTitle", { defaultValue: "Couldn't run diagnostics" }),
        message:
          e instanceof Error ? e.message : t("superAdmin.diagnostics.unknownError", { defaultValue: "Unknown error." }),
      });
    } finally {
      setRunning(false);
    }
  }

  async function handlePackage() {
    setRunning(true);
    try {
      const result = await systemSettingsApi.createDiagnosticPackage();
      setPackageResult(result);
      notifications.success({
        title: t("superAdmin.diagnostics.packageReadyTitle", { defaultValue: "Diagnostic package ready" }),
        message: t("superAdmin.diagnostics.packageReadyMessage", { defaultValue: "The audit package can now be downloaded." }),
      });
    } catch (e) {
      notifications.error({
        title: t("superAdmin.diagnostics.failedTitle", { defaultValue: "Couldn't create diagnostic package" }),
        message: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setRunning(false);
    }
  }

  async function toggleDebugLogging() {
    if (!settings) return;
    const updated = await systemSettingsApi.updateSystemSettings({ ...settings, debugLogging: !settings.debugLogging });
    setSettings(updated);
  }

  return (
    <Panel
      icon={<Stethoscope />}
      title={t("superAdmin.diagnostics.title", { defaultValue: "Diagnostics" })}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <ActionButton
            type="button"
            variant="gold"
            size="sm"
            icon={<Stethoscope />}
            onClick={() => handleRun(false)}
            disabled={running}
          >
            {running
              ? t("superAdmin.diagnostics.running", { defaultValue: "Running..." })
              : t("superAdmin.diagnostics.run", { defaultValue: "Run Diagnostics" })}
          </ActionButton>
          <ActionButton
            type="button"
            variant="ghost"
            size="sm"
            icon={<ShieldCheck />}
            onClick={() => handleRun(true)}
            disabled={running}
            title={t("superAdmin.diagnostics.runAsAdminTooltip", {
              defaultValue:
                "Requires the Windows permission prompt to succeed - reports an error instead of a limited report if it's declined.",
            })}
          >
            {t("superAdmin.diagnostics.runAsAdmin", { defaultValue: "Run Diagnostics as Admin" })}
          </ActionButton>
          <ActionButton
            type="button"
            variant="ghost"
            size="sm"
            icon={<PackageOpen />}
            onClick={handlePackage}
            disabled={running}
          >
            {t("superAdmin.diagnostics.createPackage", { defaultValue: "Create Diagnostic Package" })}
          </ActionButton>
          {settings && (
            <ActionButton
              type="button"
              variant={settings.debugLogging ? "gold" : "ghost"}
              size="sm"
              icon={<Bug />}
              onClick={toggleDebugLogging}
            >
              {settings.debugLogging
                ? t("superAdmin.diagnostics.disableDebug", { defaultValue: "Disable Debug Logging" })
                : t("superAdmin.diagnostics.enableDebug", { defaultValue: "Enable Debug Logging" })}
            </ActionButton>
          )}
        </div>
      }
    >
      <p className="mb-4 text-xs leading-relaxed text-parchment-300/50">
        {t("superAdmin.diagnostics.description", {
          defaultValue:
            'Checks the active server setup, Palworld files, local game port, Windows Firewall rules, and REST API access, then writes a support report to disk. Windows will ask for permission (a UAC prompt) since checking firewall rules needs admin rights - click "Yes" to continue.',
        })}
      </p>

      {running && (
        <p className="mb-3 animate-pulse text-xs text-life-400">
          {t("superAdmin.diagnostics.waitingForPermission", {
            defaultValue: "Waiting for the Windows permission prompt...",
          })}
        </p>
      )}

      {packageResult && (
        <div className="mb-4 flex items-center justify-between gap-3 rounded-md border border-mana-500/30 bg-mana-500/5 p-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-parchment-100">{packageResult.fileName}</p>
            <p className="truncate font-mono text-[11px] text-parchment-300/50">{packageResult.packagePath}</p>
          </div>
          <ActionButton
            type="button"
            variant="gold"
            size="sm"
            icon={<Download />}
            onClick={() => window.location.assign(packageResult.downloadUrl)}
          >
            {t("common.download", { defaultValue: "Download" })}
          </ActionButton>
        </div>
      )}

      {report && (
        <div className="space-y-2">
          <ScrollArea className="h-[360px] rounded-md border border-stone-700 bg-abyss-950/60">
            <pre className="whitespace-pre-wrap p-3 font-mono text-[11px] leading-relaxed text-parchment-200/80">
              {report}
            </pre>
          </ScrollArea>
          {reportPath && (
            <p className="truncate font-mono text-[11px] text-parchment-300/40">
              {t("superAdmin.diagnostics.savedTo", { defaultValue: "Saved to {{path}}", path: reportPath })}
            </p>
          )}
        </div>
      )}
    </Panel>
  );
}

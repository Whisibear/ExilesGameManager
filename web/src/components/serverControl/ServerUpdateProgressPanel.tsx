import { useTranslation } from "react-i18next";
import { Panel } from "@/components/ui/panel";
import type { ServerUpdateJob } from "@/types/models";

export function ServerUpdateProgressPanel({ updateJob }: { updateJob: ServerUpdateJob }) {
  const { t } = useTranslation();
  return (
    <Panel title={t("serverControl.serverUpdateTitle", { defaultValue: "Server Update" })}>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3 text-sm text-parchment-300/70">
          <span className="capitalize">
            {t("serverControl.statusLabel", {
              defaultValue: "Status: {{status}}",
              status: t(`serverControl.jobStatus.${updateJob.status}`, { defaultValue: updateJob.status }),
            })}
          </span>
          {updateJob.installedBuildId && (
            <span>
              {t("serverControl.installedBuildShort", {
                defaultValue: "Installed build {{id}}",
                id: updateJob.installedBuildId,
              })}
            </span>
          )}
          {updateJob.latestBuildId && (
            <span>
              {t("serverControl.latestBuildShort", {
                defaultValue: "Latest build {{id}}",
                id: updateJob.latestBuildId,
              })}
            </span>
          )}
        </div>
        {updateJob.log.length > 0 && (
          <div className="max-h-48 overflow-auto rounded-md border border-stone-700 bg-abyss-950/60 p-3 font-mono text-[11px] leading-relaxed text-parchment-300/55">
            {updateJob.log.slice(-12).map((line, index) => (
              <div key={`${index}-${line}`}>{line}</div>
            ))}
          </div>
        )}
      </div>
    </Panel>
  );
}

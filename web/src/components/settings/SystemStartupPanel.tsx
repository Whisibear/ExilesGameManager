import * as React from "react";
import { useTranslation } from "react-i18next";
import { Power, Save } from "lucide-react";
import { systemSettingsApi } from "@/api";
import type { SystemSettings } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { EgmToggle } from "@/components/ui/egm-toggle";
import { ActionButton } from "@/components/ui/egm-button";
import { useNotifications } from "@/hooks/useNotifications";

export function SystemStartupPanel() {
  const { t } = useTranslation();
  const [settings, setSettings] = React.useState<SystemSettings | null>(null);
  const [dirty, setDirty] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const notifications = useNotifications();

  React.useEffect(() => {
    systemSettingsApi.getSystemSettings().then(setSettings);
  }, []);

  function update(patch: Partial<SystemSettings>) {
    setSettings((prev) => (prev ? { ...prev, ...patch } : prev));
    setDirty(true);
  }

  async function handleSave() {
    if (!settings) return;
    setSaving(true);
    try {
      const saved = await systemSettingsApi.updateSystemSettings(settings);
      setSettings(saved);
      setDirty(false);
      notifications.success({
        title: t("settings.startup.savedTitle", { defaultValue: "Startup recovery saved" }),
        message: t("settings.startup.savedMessage", {
          defaultValue: "ExilesGameManager will use these options the next time Windows or the app starts.",
        }),
      });
    } catch (e) {
      notifications.error({
        title: t("settings.startup.failedTitle", { defaultValue: "Startup recovery failed" }),
        message:
          e instanceof Error ? e.message : t("settings.startup.unknownError", { defaultValue: "Unknown error." }),
      });
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <Panel icon={<Power />} title={t("settings.startup.title", { defaultValue: "Windows Startup" })}>
        <p className="animate-pulse text-sm text-parchment-300/50">
          {t("settings.startup.loading", { defaultValue: "Reading startup recovery settings..." })}
        </p>
      </Panel>
    );
  }

  return (
    <Panel icon={<Power />} title={t("settings.startup.title", { defaultValue: "Windows Startup" })}>
      <div className="space-y-4">
        <EgmToggle
          id="bootWithWindows"
          checked={settings.bootWithWindows}
          onCheckedChange={(bootWithWindows) => update({ bootWithWindows })}
          label={t("settings.startup.bootWithWindows", { defaultValue: "Start ExilesGameManager with Windows" })}
          description={t("settings.startup.bootWithWindowsDescription", {
            defaultValue: "Opens the admin tool automatically when this Windows user signs in.",
          })}
          disabled={saving}
        />
        <EgmToggle
          id="autoStartActiveServer"
          checked={settings.autoStartActiveServer}
          onCheckedChange={(autoStartActiveServer) => update({ autoStartActiveServer })}
          label={t("settings.startup.autoStartServer", {
            defaultValue: "Restart the active server when ExilesGameManager opens",
          })}
          description={t("settings.startup.autoStartServerDescription", {
            defaultValue:
              "Useful after Windows updates or power loss: when the machine comes back, the app can bring the selected server back online.",
          })}
          disabled={saving}
        />
        <div className="flex justify-end">
          <ActionButton variant="gold" icon={<Save />} onClick={handleSave} disabled={!dirty || saving}>
            {saving
              ? t("settings.startup.saving", { defaultValue: "Saving..." })
              : t("settings.startup.save", { defaultValue: "Save Startup Recovery" })}
          </ActionButton>
        </div>
      </div>
    </Panel>
  );
}

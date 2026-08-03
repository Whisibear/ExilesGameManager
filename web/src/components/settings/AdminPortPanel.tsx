import * as React from "react";
import { useTranslation } from "react-i18next";
import { Network, Save } from "lucide-react";
import { systemSettingsApi } from "@/api";
import type { SystemSettings } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActionButton } from "@/components/ui/egm-button";
import { useNotifications } from "@/hooks/useNotifications";

const MIN_PORT = 1024;
const MAX_PORT = 65535;

export function AdminPortPanel() {
  const { t } = useTranslation();
  const [settings, setSettings] = React.useState<SystemSettings | null>(null);
  const [port, setPort] = React.useState<number | null>(null);
  const [saving, setSaving] = React.useState(false);
  const notifications = useNotifications();

  React.useEffect(() => {
    systemSettingsApi.getSystemSettings().then((s) => {
      setSettings(s);
      setPort(s.adminPort);
    });
  }, []);

  function handlePortChange(value: string) {
    const parsed = parseInt(value, 10);
    setPort(Number.isNaN(parsed) ? null : parsed);
  }

  const dirty = settings !== null && port !== null && port !== settings.adminPort;
  const valid = port !== null && port >= MIN_PORT && port <= MAX_PORT;

  async function handleSave() {
    if (!settings || port === null || !valid) return;
    setSaving(true);
    try {
      const saved = await systemSettingsApi.updateSystemSettings({ ...settings, adminPort: port });
      setSettings(saved);
      setPort(saved.adminPort);
      notifications.success({
        title: t("superAdmin.adminPort.savedTitle", { defaultValue: "Admin panel port saved" }),
        message: t("superAdmin.adminPort.savedMessage", {
          defaultValue: "Restart ExilesGameManager for the new port to take effect.",
        }),
      });
    } catch (e) {
      notifications.error({
        title: t("superAdmin.adminPort.failedTitle", { defaultValue: "Couldn't save port" }),
        message:
          e instanceof Error ? e.message : t("superAdmin.adminPort.unknownError", { defaultValue: "Unknown error." }),
      });
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <Panel icon={<Network />} title={t("superAdmin.adminPort.title", { defaultValue: "Admin Panel Port" })}>
        <p className="animate-pulse text-sm text-parchment-300/50">
          {t("superAdmin.adminPort.loading", { defaultValue: "Reading admin panel port..." })}
        </p>
      </Panel>
    );
  }

  return (
    <Panel icon={<Network />} title={t("superAdmin.adminPort.title", { defaultValue: "Admin Panel Port" })}>
      <p className="mb-4 text-xs leading-relaxed text-parchment-300/50">
        {t("superAdmin.adminPort.description", {
          defaultValue:
            "The port this admin panel itself listens on (default 8000) - separate from the Palworld game server's own port. Changing it can help if something else on this PC already uses 8000, or just to make this panel a less predictable target for random port scans.",
        })}
      </p>
      <div className="flex items-end gap-2">
        <div>
          <Label htmlFor="admin-port">{t("superAdmin.adminPort.label", { defaultValue: "Port" })}</Label>
          <Input
            id="admin-port"
            type="number"
            min={MIN_PORT}
            max={MAX_PORT}
            value={port ?? ""}
            onChange={(e) => handlePortChange(e.target.value)}
            className="max-w-[10rem]"
            disabled={saving}
          />
        </div>
        <ActionButton
          type="button"
          variant="gold"
          size="sm"
          icon={<Save />}
          onClick={handleSave}
          disabled={!dirty || !valid || saving}
        >
          {saving
            ? t("superAdmin.adminPort.saving", { defaultValue: "Saving..." })
            : t("superAdmin.adminPort.save", { defaultValue: "Save" })}
        </ActionButton>
      </div>
      {port !== null && !valid && (
        <p className="mt-2 text-xs text-blood-400">
          {t("superAdmin.adminPort.invalidRange", {
            defaultValue: "Port must be between {{min}} and {{max}}.",
            min: MIN_PORT,
            max: MAX_PORT,
          })}
        </p>
      )}
      <p className="mt-3 text-[11px] leading-relaxed text-parchment-300/35">
        {t("superAdmin.adminPort.restartHint", {
          defaultValue:
            "Saving updates the setting immediately, but the app keeps running on the old port until you restart it (close and reopen ExilesGameManager). Firewall/Remote Access below need to be re-allowed for the new port after that.",
        })}
      </p>
    </Panel>
  );
}

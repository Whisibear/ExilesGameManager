import * as React from "react";
import { useTranslation } from "react-i18next";
import { HardDrive } from "lucide-react";
import { instancesApi } from "@/api";
import type { ServerInstance } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { AdminPortPanel } from "@/components/settings/AdminPortPanel";
import { RemoteAccessPanel } from "@/components/settings/RemoteAccessPanel";
import { PortForwardPanel } from "@/components/settings/PortForwardPanel";
import { LocalApiSettingsPanel } from "@/components/settings/LocalApiSettingsPanel";
import { DiagnosticsPanel } from "@/components/settings/DiagnosticsPanel";
import { PrivacyModePanel } from "@/components/settings/PrivacyModePanel";
import { NexusIntegrationPanel } from "@/components/settings/NexusIntegrationPanel";
import { SteamCmdAccess } from "@/components/mods/SteamCmdAccess";
import { FirewallManagerPanel } from "@/components/settings/FirewallManagerPanel";
import { AppUpdatePanel } from "@/components/settings/AppUpdatePanel";

export default function SuperAdmin() {
  const { t } = useTranslation();
  const [instance, setInstance] = React.useState<ServerInstance | null>(null);
  const [steamCmdOpen, setSteamCmdOpen] = React.useState(false);

  React.useEffect(() => {
    instancesApi.getActive().then(setInstance);
  }, []);

  return (
    <div className="space-y-6">
      <p className="text-xs leading-relaxed text-parchment-300/50">
        {t("superAdmin.intro", {
          defaultValue:
            "Anything here changes this machine's network exposure, who can reach it, or what external accounts it's connected to, and is reserved for the super admin, same as account management.",
        })}
      </p>

      {instance && (
        <Panel icon={<HardDrive />} title={t("superAdmin.activeServer", { defaultValue: "Active Server" })}>
          <p className="truncate text-sm text-parchment-300/70">
            {instance.name} &middot; <span className="font-mono text-xs">{instance.serverPath}</span>
          </p>
        </Panel>
      )}

      <AppUpdatePanel />
      <LocalApiSettingsPanel />
      <PrivacyModePanel />
      <FirewallManagerPanel />
      <PortForwardPanel />
      <AdminPortPanel />
      <RemoteAccessPanel />
      <DiagnosticsPanel />
      <NexusIntegrationPanel />
      <SteamCmdAccess open={steamCmdOpen} onOpenChange={setSteamCmdOpen} />
    </div>
  );
}

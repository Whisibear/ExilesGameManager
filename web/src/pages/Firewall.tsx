import { useTranslation } from "react-i18next";
import { ShieldCheck } from "lucide-react";
import { Panel } from "@/components/ui/panel";
import { FirewallManagerPanel } from "@/components/settings/FirewallManagerPanel";

export default function Firewall() {
  const { t } = useTranslation();
  return <div className="space-y-6">
    <Panel icon={<ShieldCheck />} title={t("firewall.title", { defaultValue: "Firewall Management" })}>
      <p className="text-sm text-parchment-300/70">{t("firewall.description", { defaultValue: "Inspect, synchronize, repair, and remove the Windows Firewall rules for every managed server." })}</p>
    </Panel>
    <FirewallManagerPanel />
  </div>;
}

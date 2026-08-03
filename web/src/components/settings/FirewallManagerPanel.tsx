import * as React from "react";
import { ShieldCheck, RefreshCw, Trash2, Wrench } from "lucide-react";
import { networkApi } from "@/api";
import type { InstanceFirewallStatus } from "@/types/models";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";
import { useNotifications } from "@/hooks/useNotifications";

export function FirewallManagerPanel() {
  const [rows, setRows] = React.useState<InstanceFirewallStatus[]>([]);
  const [busy, setBusy] = React.useState(false);
  const notifications = useNotifications();
  const load = React.useCallback(() => networkApi.getInstanceFirewallStatus().then((r) => setRows(r.instances)), []);
  React.useEffect(() => { load(); }, [load]);

  async function run(action: () => Promise<unknown>, success: string) {
    setBusy(true);
    try { await action(); await load(); notifications.success({ title: success, message: "Windows Firewall rules are synchronized." }); }
    catch (e) { notifications.error({ title: "Firewall operation failed", message: e instanceof Error ? e.message : "Unknown error" }); }
    finally { setBusy(false); }
  }

  return <Panel icon={<ShieldCheck />} title="Windows Firewall — All Servers">
    <div className="mb-4 flex flex-wrap gap-2">
      <ActionButton variant="gold" size="sm" icon={<Wrench />} disabled={busy} onClick={() => run(networkApi.syncAllInstanceFirewallRules, "Firewall synchronized")}>Synchronize All</ActionButton>
      <ActionButton variant="ghost" size="sm" icon={<RefreshCw />} disabled={busy} onClick={load}>Refresh</ActionButton>
    </div>
    <div className="space-y-3">
      {rows.map((row) => <div key={row.instanceId} className="rounded-md border border-stone-700/70 bg-stone-950/30 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div><b className="text-parchment-100">{row.instanceName}</b><span className={`ml-3 text-xs ${row.healthy ? "text-emerald-400" : "text-red-400"}`}>{row.healthy ? "All rules active" : "Rules missing"}</span></div>
          <div className="flex gap-2">
            <ActionButton size="sm" variant="ghost" disabled={busy} onClick={() => run(() => networkApi.syncInstanceFirewallRules(row.instanceId), "Server rules synchronized")}>Repair</ActionButton>
            <ActionButton size="sm" variant="danger" icon={<Trash2 />} disabled={busy} onClick={() => run(() => networkApi.removeInstanceFirewallRules(row.instanceId), "Server rules removed")}>Remove Rules</ActionButton>
          </div>
        </div>
        <div className="mt-2 grid gap-1 text-xs font-mono text-parchment-300/60">
          {row.rules.map((rule) => <div key={rule.name}><span className={rule.exists ? "text-emerald-400" : "text-red-400"}>{rule.exists ? "●" : "●"}</span> {rule.protocol} {rule.port} — {rule.name}</div>)}
        </div>
      </div>)}
    </div>
  </Panel>;
}

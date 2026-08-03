import * as React from "react";
import { useTranslation } from "react-i18next";
import { FolderOpen, RotateCcw } from "lucide-react";
import { instancesApi } from "@/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActionButton } from "@/components/ui/egm-button";
import { SpaceInvadersGame } from "@/components/fantasy/SpaceInvadersGame";
import { useNotifications } from "@/hooks/useNotifications";

interface DeployServerWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeployed: () => void;
}

type WizardStatus = "idle" | "running" | "done" | "error";

export function DeployServerWizard({ open, onOpenChange, onDeployed }: DeployServerWizardProps) {
  const { t } = useTranslation();
  const [name, setName] = React.useState("");
  const [gamePort, setGamePort] = React.useState(8211);
  const [rconPort, setRconPort] = React.useState(8212);
  const [queryPort, setQueryPort] = React.useState(8213);
  const [maxPlayers, setMaxPlayers] = React.useState(32);
  const [installParentDir, setInstallParentDir] = React.useState("");
  const [defaultLocation, setDefaultLocation] = React.useState<string | null>(null);
  const [templateInstanceId, setTemplateInstanceId] = React.useState("");
  const [instances, setInstances] = React.useState<Array<{ id: string; name: string }>>([]);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [log, setLog] = React.useState<string[]>([]);
  const [status, setStatus] = React.useState<WizardStatus>("idle");
  const [error, setError] = React.useState<string | null>(null);
  const notifications = useNotifications();
  const logEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) {
      setJobId(null);
      setLog([]);
      setStatus("idle");
      setError(null);
      setInstallParentDir("");
      setTemplateInstanceId("");
      return;
    }
    instancesApi.list().then((data) => {
      setInstances(data.instances.map((item) => ({ id: item.id, name: item.name })));
      const used = new Set<number>();
      data.instances.forEach((item) => { used.add(item.gamePort); used.add(item.rconPort); if (item.queryPort) used.add(item.queryPort); });
      let game = 8211;
      while (used.has(game) || used.has(game + 1) || used.has(game + 2)) game += 3;
      setGamePort(game);
      setRconPort(game + 1);
      setQueryPort(game + 2);
    }).catch(() => setInstances([]));
    instancesApi
      .getDefaultDeployLocation()
      .then((data) => setDefaultLocation(data.path))
      .catch(() => setDefaultLocation(null));
  }, [open]);

  React.useEffect(() => {
    if (!jobId || status !== "running") return;
    const interval = setInterval(async () => {
      const job = await instancesApi.getDeployStatus(jobId);
      setLog(job.log);
      if (job.status === "done") {
        setStatus("done");
        notifications.success({
          title: t("settings.deploy.deployedTitle", { defaultValue: "Server deployed" }),
          message: t("settings.deploy.deployedMessage", { defaultValue: "{{name}} is ready.", name }),
        });
        onDeployed();
      } else if (job.status === "error") {
        setStatus("error");
        setError(job.error);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [jobId, status, name, notifications, onDeployed, t]);

  React.useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  async function handleDeploy() {
    setStatus("running");
    setError(null);
    setLog([]);
    try {
      const { jobId: id } = await instancesApi.deploy({
        name: name.trim(),
        gamePort,
        rconPort,
        queryPort,
        maxPlayers,
        installParentDir: installParentDir.trim() || null,
        templateInstanceId: templateInstanceId || null,
      });
      setJobId(id);
    } catch (e) {
      setStatus("error");
      setError(
        e instanceof Error
          ? e.message
          : t("settings.deploy.startFailedFallback", { defaultValue: "Couldn't start the deploy." })
      );
    }
  }

  function handleClose(next: boolean) {
    if (!next && status === "running") return; // don't let them close mid-deploy
    onOpenChange(next);
  }

  async function handleBrowseInstallLocation() {
    setError(null);
    try {
      const { path } = await instancesApi.browseDeployParentDir();
      if (path) setInstallParentDir(path);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : t("settings.deploy.folderPickerFailedFallback", { defaultValue: "Couldn't open the folder picker." })
      );
    }
  }

  const canSubmit = !!name.trim() && status === "idle";

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("settings.deploy.title", { defaultValue: "Deploy a New Server" })}</DialogTitle>
          <DialogDescription>
            {t("settings.deploy.description", {
              defaultValue:
                "Creates a fully isolated Palworld Dedicated Server either through SteamCMD or as a clean local copy of an existing stopped instance. Missing Windows Firewall rules are created automatically with one normal UAC consent prompt.",
            })}
          </DialogDescription>
        </DialogHeader>

        {status === "idle" && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="deploy-source">Creation Method</Label>
              <select
                id="deploy-source"
                value={templateInstanceId}
                onChange={(e) => setTemplateInstanceId(e.target.value)}
                className="h-10 w-full rounded-md border border-stone-700 bg-abyss-950/60 px-3 text-sm text-parchment-100"
              >
                <option value="">Fresh download via SteamCMD</option>
                {instances.map((instance) => (
                  <option key={instance.id} value={instance.id}>Clean local copy of: {instance.name}</option>
                ))}
              </select>
              <p className="text-[11px] leading-relaxed text-parchment-300/40">
                A local copy reuses the server binaries and excludes saves, mods, logs and instance runtime data. The source server must be stopped.
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="deploy-name">{t("settings.deploy.serverName", { defaultValue: "Server Name" })}</Label>
              <Input
                id="deploy-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("settings.deploy.serverNamePlaceholder", { defaultValue: "My Cozy Palworld" })}
                autoFocus
              />
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="space-y-1.5">
                <Label htmlFor="deploy-port">{t("settings.deploy.gamePort", { defaultValue: "Game Port" })}</Label>
                <Input
                  id="deploy-port"
                  type="number"
                  value={gamePort}
                  onChange={(e) => setGamePort(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="deploy-rcon">
                  {t("settings.deploy.restApiPort", { defaultValue: "REST API Port" })}
                </Label>
                <Input
                  id="deploy-rcon"
                  type="number"
                  value={rconPort}
                  onChange={(e) => setRconPort(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="deploy-query">
                  {t("settings.deploy.queryPort", { defaultValue: "Steam Query Port" })}
                </Label>
                <Input
                  id="deploy-query"
                  type="number"
                  value={queryPort}
                  onChange={(e) => setQueryPort(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="deploy-max">{t("settings.deploy.maxPlayers", { defaultValue: "Max Players" })}</Label>
                <Input
                  id="deploy-max"
                  type="number"
                  value={maxPlayers}
                  onChange={(e) => setMaxPlayers(Number(e.target.value))}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="deploy-location">
                {t("settings.deploy.installLocation", { defaultValue: "Server Deployment Location" })}
              </Label>
              <div className="flex gap-2">
                <Input
                  id="deploy-location"
                  value={
                    installParentDir ||
                    t("settings.deploy.defaultFolder", { defaultValue: "Default ExilesGameManager servers folder" })
                  }
                  readOnly
                  className="flex-1"
                />
                {installParentDir && (
                  <ActionButton
                    type="button"
                    variant="ghost"
                    size="sm"
                    icon={<RotateCcw />}
                    onClick={() => setInstallParentDir("")}
                  >
                    {t("settings.deploy.default", { defaultValue: "Default" })}
                  </ActionButton>
                )}
                <ActionButton
                  type="button"
                  variant="ghost"
                  size="sm"
                  icon={<FolderOpen />}
                  onClick={handleBrowseInstallLocation}
                >
                  {t("settings.deploy.browse", { defaultValue: "Browse" })}
                </ActionButton>
              </div>
              {!installParentDir && defaultLocation && (
                <p className="truncate font-mono text-[11px] text-parchment-300/40">
                  {t("settings.deploy.defaultLocationValue", {
                    defaultValue: "Default: {{path}}",
                    path: defaultLocation,
                  })}
                </p>
              )}
            </div>
            <p className="text-[11px] leading-relaxed text-parchment-300/40">
              {t("settings.deploy.hint", {
                defaultValue:
                  "ExilesGameManager creates a separate server folder, validates unique ports and configures the Windows Firewall automatically. On Windows 11 approve the UAC dialog; an elevated Windows Server 2022 service needs no extra prompt.",
              })}
            </p>
          </div>
        )}

        {status !== "idle" && (
          <div className="space-y-3">
            {status === "running" && (
              <SpaceInvadersGame
                shipStyle="squid"
                caption={t("settings.deploy.waitGameCaption", {
                  defaultValue: "Use ← → and Space while your server downloads...",
                })}
              />
            )}
            <div className="h-48 overflow-y-auto rounded-md border border-stone-700 bg-abyss-950/60 p-3 font-mono text-[11px] leading-relaxed text-parchment-300/70">
              {log.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
              <div ref={logEndRef} />
            </div>
            {status === "running" && (
              <p className="animate-pulse text-xs text-life-400">
                {t("settings.deploy.deploying", { defaultValue: "Deploying..." })}
              </p>
            )}
            {status === "done" && (
              <p className="text-xs text-life-400">
                {t("settings.deploy.done", { defaultValue: "Done - the new server is now active." })}
              </p>
            )}
            {status === "error" && <p className="text-xs text-blood-400">{error}</p>}
          </div>
        )}

        <DialogFooter>
          {status === "idle" && (
            <>
              <ActionButton variant="ghost" onClick={() => onOpenChange(false)}>
                {t("settings.deploy.cancel", { defaultValue: "Cancel" })}
              </ActionButton>
              <ActionButton variant="gold" onClick={handleDeploy} disabled={!canSubmit}>
                {t("settings.deploy.deploy", { defaultValue: "Deploy" })}
              </ActionButton>
            </>
          )}
          {status === "running" && (
            <ActionButton variant="ghost" disabled>
              {t("settings.deploy.deploying", { defaultValue: "Deploying..." })}
            </ActionButton>
          )}
          {(status === "done" || status === "error") && (
            <ActionButton variant="gold" onClick={() => onOpenChange(false)}>
              {t("settings.deploy.close", { defaultValue: "Close" })}
            </ActionButton>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

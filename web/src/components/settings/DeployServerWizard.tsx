import * as React from "react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { FolderOpen, Gamepad2, RotateCcw, Server, ShieldAlert } from "lucide-react";
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
import { FALLBACK_GAME_CATALOG } from "@/lib/gameCatalogFallback";
import type {
  GameDefinition,
  GamePortDefinition,
  ServerInstance,
} from "@/types/models";

interface DeployServerWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeployed: () => void;
}

type WizardStatus = "idle" | "running" | "done" | "error";
type PortValues = Record<string, number>;

function gameDescription(game: GameDefinition | null, t: TFunction): string {
  if (!game) return t("settings.deploy.descriptionGeneric");
  if (game.id === "palworld") return t("settings.deploy.descriptionPalworld");
  if (game.id === "conan_exiles_enhanced") return t("settings.deploy.descriptionConanEnhanced");
  return t("settings.deploy.descriptionConanLegacy");
}

function gamePlaceholder(game: GameDefinition | null, t: TFunction): string {
  if (!game) return t("settings.deploy.placeholderGeneric");
  if (game.id === "palworld") return t("settings.deploy.placeholderPalworld");
  if (game.id === "conan_exiles_enhanced") return t("settings.deploy.placeholderConanEnhanced");
  return t("settings.deploy.placeholderConanLegacy");
}

export function DeployServerWizard({ open, onOpenChange, onDeployed }: DeployServerWizardProps) {
  const { t } = useTranslation();
  const [name, setName] = React.useState("");
  const [games, setGames] = React.useState<GameDefinition[]>(FALLBACK_GAME_CATALOG.games);
  const [gameId, setGameId] = React.useState("palworld");
  const [ports, setPorts] = React.useState<PortValues>({});
  const [maxPlayers, setMaxPlayers] = React.useState(32);
  const [installParentDir, setInstallParentDir] = React.useState("");
  const [defaultLocation, setDefaultLocation] = React.useState<string | null>(null);
  const [templateInstanceId, setTemplateInstanceId] = React.useState("");
  const [instances, setInstances] = React.useState<ServerInstance[]>([]);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [log, setLog] = React.useState<string[]>([]);
  const [status, setStatus] = React.useState<WizardStatus>("idle");
  const [error, setError] = React.useState<string | null>(null);
  const notifications = useNotifications();
  const logEndRef = React.useRef<HTMLDivElement>(null);

  const selectedGame = games.find((game) => game.id === gameId) ?? null;
  const compatibleInstances = instances.filter((instance) => instance.gameId === gameId);

  React.useEffect(() => {
    if (!open) {
      setJobId(null);
      setLog([]);
      setStatus("idle");
      setError(null);
      setName("");
      setInstallParentDir("");
      setTemplateInstanceId("");
      setGameId("palworld");
      setPorts({});
      return;
    }

    instancesApi
      .list()
      .then((instanceData) => setInstances(instanceData.instances))
      .catch(() => setInstances([]));

    instancesApi
      .listGames()
      .then((gameData) => {
        setGames(gameData.games);
        setGameId(gameData.defaultGameId);
      })
      .catch(() => {
        setGames(FALLBACK_GAME_CATALOG.games);
        setGameId(FALLBACK_GAME_CATALOG.defaultGameId);
      });

    instancesApi
      .getDefaultDeployLocation()
      .then((data) => setDefaultLocation(data.path))
      .catch(() => setDefaultLocation(null));
  }, [open]);

  React.useEffect(() => {
    if (!open || !gameId) return;
    setTemplateInstanceId("");
    setError(null);
    instancesApi
      .suggestDeployPorts(gameId)
      .then((result) => {
        setPorts(Object.fromEntries(result.ports.map((item) => [item.key, item.port])));
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [gameId, open]);

  React.useEffect(() => {
    if (!jobId || status !== "running") return;
    const interval = window.setInterval(async () => {
      const job = await instancesApi.getDeployStatus(jobId);
      setLog(job.log);
      if (job.status === "done") {
        setStatus("done");
        notifications.success({
          title: t("settings.deploy.deployedTitle"),
          message: t("settings.deploy.deployedMessage", { name }),
        });
        onDeployed();
      } else if (job.status === "error") {
        setStatus("error");
        setError(job.error);
      }
    }, 1500);
    return () => window.clearInterval(interval);
  }, [jobId, status, name, notifications, onDeployed, t]);

  React.useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  function updatePort(definition: GamePortDefinition, value: number) {
    setPorts((current) => {
      const next = { ...current, [definition.key]: value };
      for (const candidate of selectedGame?.portDefinitions ?? []) {
        if (candidate.relative_to === definition.key) {
          next[candidate.key] = value + candidate.offset;
        }
      }
      return next;
    });
  }

  async function handleDeploy() {
    if (!selectedGame?.deployable) return;
    setStatus("running");
    setError(null);
    setLog([]);
    try {
      const { jobId: id } = await instancesApi.deploy({
        name: name.trim(),
        gameId,
        gamePort: ports.game,
        rconPort: ports.restApi ?? ports.rcon,
        queryPort: ports.query,
        maxPlayers,
        installParentDir: installParentDir.trim() || null,
        templateInstanceId: templateInstanceId || null,
      });
      setJobId(id);
    } catch (reason) {
      setStatus("error");
      setError(reason instanceof Error ? reason.message : t("settings.deploy.startFailedFallback"));
    }
  }

  function handleClose(next: boolean) {
    if (!next && status === "running") return;
    onOpenChange(next);
  }

  async function handleBrowseInstallLocation() {
    setError(null);
    try {
      const { path } = await instancesApi.browseDeployParentDir();
      if (path) setInstallParentDir(path);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("settings.deploy.folderPickerFailedFallback"));
    }
  }

  const canSubmit =
    Boolean(name.trim()) &&
    status === "idle" &&
    Boolean(selectedGame?.deployable) &&
    selectedGame?.portDefinitions.every((definition) => Boolean(ports[definition.key])) === true;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t("settings.deploy.title")}</DialogTitle>
          <DialogDescription>{gameDescription(selectedGame, t)}</DialogDescription>
        </DialogHeader>

        {status === "idle" && (
          <div className="space-y-5">
            <section className="space-y-2" data-egm-feature="multi-game-selector-d2">
              <Label>{t("settings.deploy.gameSelection")}</Label>
              <div className="grid gap-2 sm:grid-cols-3">
                {games.map((game) => {
                  const active = game.id === gameId;
                  return (
                    <button
                      key={game.id}
                      type="button"
                      onClick={() => setGameId(game.id)}
                      className={`rounded-xl border p-3 text-left transition ${
                        active
                          ? "border-mana-400 bg-mana-500/10 shadow-[0_0_18px_rgba(0,210,255,0.08)]"
                          : "border-stone-700 bg-abyss-950/40 hover:border-stone-600"
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        <div className={`mt-0.5 rounded-lg border p-1.5 ${active ? "border-mana-400/50 text-mana-300" : "border-stone-700 text-parchment-300/50"}`}>
                          {game.family === "conan_exiles" ? <Server className="h-4 w-4" /> : <Gamepad2 className="h-4 w-4" />}
                        </div>
                        <div className="min-w-0">
                          <div className="font-semibold text-parchment-100">{game.label}</div>
                          <div className="mt-1 text-[11px] text-parchment-300/50">
                            {game.deployable
                              ? t("settings.deploy.availableNow")
                              : t("settings.deploy.preparedNotInstallable")}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
              {selectedGame && !selectedGame.deployable && (
                <div className="flex gap-2 rounded-lg border border-gold-500/25 bg-gold-500/5 p-3 text-xs text-gold-200/80">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{t("settings.deploy.providerPending")}</span>
                </div>
              )}
            </section>

            <div className="space-y-1.5">
              <Label htmlFor="deploy-source">{t("settings.deploy.creationMethod")}</Label>
              <select
                id="deploy-source"
                value={templateInstanceId}
                onChange={(event) => setTemplateInstanceId(event.target.value)}
                className="h-10 w-full rounded-md border border-stone-700 bg-abyss-950/60 px-3 text-sm text-parchment-100"
              >
                <option value="">{t("settings.deploy.freshSteamCmd")}</option>
                {compatibleInstances.map((instance) => (
                  <option key={instance.id} value={instance.id}>
                    {t("settings.deploy.cleanCopyOf", { name: instance.name })}
                  </option>
                ))}
              </select>
              <p className="text-[11px] leading-relaxed text-parchment-300/40">
                {t("settings.deploy.cloneHint")}
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="deploy-name">{t("settings.deploy.serverName")}</Label>
              <Input
                id="deploy-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder={gamePlaceholder(selectedGame, t)}
                autoFocus
              />
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {(selectedGame?.portDefinitions ?? []).map((definition) => (
                <div key={definition.key} className="space-y-1.5">
                  <Label htmlFor={`deploy-port-${definition.key}`}>
                    {definition.label}
                    <span className="ml-1 text-[10px] text-parchment-300/35">{definition.protocol}</span>
                  </Label>
                  <Input
                    id={`deploy-port-${definition.key}`}
                    type="number"
                    value={ports[definition.key] ?? definition.default}
                    disabled={!definition.configurable}
                    onChange={(event) => updatePort(definition, Number(event.target.value))}
                  />
                </div>
              ))}
              <div className="space-y-1.5">
                <Label htmlFor="deploy-max">{t("settings.deploy.maxPlayers")}</Label>
                <Input
                  id="deploy-max"
                  type="number"
                  min={1}
                  value={maxPlayers}
                  onChange={(event) => setMaxPlayers(Number(event.target.value))}
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="deploy-location">{t("settings.deploy.installLocation")}</Label>
              <div className="flex gap-2">
                <Input
                  id="deploy-location"
                  value={installParentDir || t("settings.deploy.defaultFolder")}
                  readOnly
                  className="flex-1"
                />
                {installParentDir && (
                  <ActionButton type="button" variant="ghost" size="sm" icon={<RotateCcw />} onClick={() => setInstallParentDir("")}>
                    {t("settings.deploy.default")}
                  </ActionButton>
                )}
                <ActionButton type="button" variant="ghost" size="sm" icon={<FolderOpen />} onClick={handleBrowseInstallLocation}>
                  {t("settings.deploy.browse")}
                </ActionButton>
              </div>
              {!installParentDir && defaultLocation && (
                <p className="truncate font-mono text-[11px] text-parchment-300/40">
                  {t("settings.deploy.defaultLocationValue", { path: defaultLocation })}
                </p>
              )}
            </div>

            <p className="text-[11px] leading-relaxed text-parchment-300/40">
              {t("settings.deploy.hintMultiGame")}
            </p>
            {error && <p className="text-xs text-blood-400">{error}</p>}
          </div>
        )}

        {status !== "idle" && (
          <div className="space-y-3">
            {status === "running" && (
              <SpaceInvadersGame shipStyle="squid" caption={t("settings.deploy.waitGameCaption")} />
            )}
            <div className="h-48 overflow-y-auto rounded-md border border-stone-700 bg-abyss-950/60 p-3 font-mono text-[11px] leading-relaxed text-parchment-300/70">
              {log.map((line, index) => <div key={index}>{line}</div>)}
              <div ref={logEndRef} />
            </div>
            {status === "running" && <p className="animate-pulse text-xs text-life-400">{t("settings.deploy.deploying")}</p>}
            {status === "done" && <p className="text-xs text-life-400">{t("settings.deploy.done")}</p>}
            {status === "error" && <p className="text-xs text-blood-400">{error}</p>}
          </div>
        )}

        <DialogFooter>
          {status === "idle" && (
            <>
              <ActionButton variant="ghost" onClick={() => onOpenChange(false)}>{t("settings.deploy.cancel")}</ActionButton>
              <ActionButton variant="gold" onClick={handleDeploy} disabled={!canSubmit}>{t("settings.deploy.deploy")}</ActionButton>
            </>
          )}
          {status === "running" && <ActionButton variant="ghost" disabled>{t("settings.deploy.deploying")}</ActionButton>}
          {(status === "done" || status === "error") && (
            <ActionButton variant="gold" onClick={() => onOpenChange(false)}>{t("settings.deploy.close")}</ActionButton>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

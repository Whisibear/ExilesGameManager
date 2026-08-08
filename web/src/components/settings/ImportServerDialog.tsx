import * as React from "react";
import { useTranslation } from "react-i18next";
import { FolderOpen, Radar } from "lucide-react";
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
import { useNotifications } from "@/hooks/useNotifications";
import type { GameDefinition } from "@/types/models";
import { FALLBACK_GAME_CATALOG } from "@/lib/gameCatalogFallback";

interface ImportServerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported: () => void;
}

export function ImportServerDialog({ open, onOpenChange, onImported }: ImportServerDialogProps) {
  const { t } = useTranslation();
  const [name, setName] = React.useState("");
  const [games, setGames] = React.useState<GameDefinition[]>(FALLBACK_GAME_CATALOG.games);
  const [gameId, setGameId] = React.useState("palworld");
  const [path, setPath] = React.useState("");
  const [detecting, setDetecting] = React.useState(false);
  const [importing, setImporting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const notifications = useNotifications();

  React.useEffect(() => {
    if (!open) {
      setName("");
      setPath("");
      setError(null);
      setGameId("palworld");
      return;
    }
    instancesApi.listGames()
      .then((catalog) => {
        setGames(catalog.games);
        setGameId(catalog.defaultGameId);
      })
      .catch(() => {
        setGames(FALLBACK_GAME_CATALOG.games);
        setGameId(FALLBACK_GAME_CATALOG.defaultGameId);
      });
  }, [open]);

  async function handleDetect() {
    setDetecting(true);
    setError(null);
    try {
      const result = await instancesApi.importDetected();
      if (!result.detected) {
        setError(result.message || t("settings.import.notDetected", { defaultValue: "No existing server installation was detected. Select a server folder manually." }));
        return;
      }
      notifications.success({
        title: t("settings.import.importedTitle", { defaultValue: "Server imported" }),
        message: t("settings.import.detectedMessage", { defaultValue: "Found and registered via your Steam library." }),
      });
      onImported();
      onOpenChange(false);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : t("settings.import.detectFailedFallback", {
              defaultValue: "Couldn't find a Palworld server in any Steam library.",
            })
      );
    } finally {
      setDetecting(false);
    }
  }

  async function handleBrowse() {
    const { path: picked } = await instancesApi.browseImportDir();
    if (picked) setPath(picked);
  }

  async function handleImport() {
    setImporting(true);
    setError(null);
    try {
      const result = await instancesApi.importExisting(name.trim(), path.trim(), gameId);
      notifications.success({
        title: t("settings.import.importedTitle", { defaultValue: "Server imported" }),
        message: name.trim(),
      });
      for (const issue of result.importAnalysis?.issues ?? []) {
        const payload = {
          title: t(issue.titleKey, { defaultValue: issue.fallbackTitle }),
          message: t(issue.messageKey, { defaultValue: issue.fallbackMessage }),
        };
        if (issue.severity === "error") notifications.error(payload);
        else if (issue.severity === "warning") notifications.warning(payload);
        else notifications.info(payload);
      }
      onImported();
      onOpenChange(false);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : t("settings.import.importFailedFallback", { defaultValue: "Couldn't import that folder." })
      );
    } finally {
      setImporting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{t("settings.import.title", { defaultValue: "Import an Existing Server" })}</DialogTitle>
          <DialogDescription>
            {t("settings.import.description", {
              defaultValue: "Register an existing dedicated server. EGM validates the selected game layout before importing it.",
            })}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="import-game">Game</Label>
            <select id="import-game" value={gameId} onChange={(event) => setGameId(event.target.value)}
              className="h-10 w-full rounded-md border border-stone-700 bg-abyss-950/60 px-3 text-sm text-parchment-100">
              {games.map((game) => (
                <option key={game.id} value={game.id} disabled={!game.deployable}>
                  {game.label}{!game.deployable ? " — prepared, not yet importable" : ""}
                </option>
              ))}
            </select>
          </div>
          <ActionButton
            type="button"
            variant="mana"
            icon={<Radar />}
            onClick={handleDetect}
            disabled={detecting || gameId !== "palworld"}
            className="w-full"
          >
            {detecting
              ? t("settings.import.scanning", { defaultValue: "Scanning Steam libraries..." })
              : t("settings.import.autoDetect", { defaultValue: "Auto-Detect via Steam" })}
          </ActionButton>

          <div className="flex items-center gap-3 text-[11px] uppercase tracking-wide text-parchment-300/40">
            <div className="h-px flex-1 bg-stone-700" />{" "}
            {t("settings.import.orManually", { defaultValue: "or enter manually" })}{" "}
            <div className="h-px flex-1 bg-stone-700" />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="import-name">{t("settings.import.serverName", { defaultValue: "Server Name" })}</Label>
            <Input
              id="import-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("settings.import.serverNamePlaceholder", { defaultValue: "My Game Server" })}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="import-path">
              {t("settings.import.installFolder", { defaultValue: "Install Folder" })}
            </Label>
            <div className="flex gap-2">
              <Input
                id="import-path"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                placeholder={gameId.startsWith("conan_exiles") ? "C:\\ConanServer" : "D:\\SteamLibrary\\steamapps\\common\\PalServer"}
                className="flex-1"
              />
              <ActionButton type="button" variant="ghost" size="sm" icon={<FolderOpen />} onClick={handleBrowse}>
                {t("settings.import.browse", { defaultValue: "Browse" })}
              </ActionButton>
            </div>
          </div>
        </div>

        {error && <p className="text-xs text-blood-400">{error}</p>}

        <DialogFooter>
          <ActionButton variant="ghost" onClick={() => onOpenChange(false)}>
            {t("settings.import.cancel", { defaultValue: "Cancel" })}
          </ActionButton>
          <ActionButton variant="gold" onClick={handleImport} disabled={importing || !name.trim() || !path.trim()}>
            {importing
              ? t("settings.import.importing", { defaultValue: "Importing..." })
              : t("settings.import.import", { defaultValue: "Import" })}
          </ActionButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

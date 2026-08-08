
import * as React from "react";
import { Terminal, Trash2, Send } from "lucide-react";
import { useTranslation } from "react-i18next";
import { serverApi } from "@/api";
import { Panel } from "@/components/ui/panel";
import { ActionButton } from "@/components/ui/egm-button";

const MAX_BUFFER = 200_000;

export function ConanLiveConsole({ online }: { online: boolean }) {
  const { t } = useTranslation();
  const [cursor, setCursor] = React.useState<number | undefined>(undefined);
  const [output, setOutput] = React.useState("");
  const [command, setCommand] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [available, setAvailable] = React.useState(false);
  const [rconReady, setRconReady] = React.useState(false);
  const [rconStatusText, setRconStatusText] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const viewportRef = React.useRef<HTMLPreElement>(null);

  React.useEffect(() => {
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        const chunk = await serverApi.getLiveConsole(cursor);
        if (cancelled) return;
        setAvailable(chunk.available);
        setError(null);
        setCursor(chunk.cursor);
        if (chunk.reset) {
          setOutput(chunk.text.slice(-MAX_BUFFER));
        } else if (chunk.text) {
          setOutput((current) => (current + chunk.text).slice(-MAX_BUFFER));
        }
      } catch (reason) {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      } finally {
        if (!cancelled) timer = window.setTimeout(poll, 1500);
      }
    };

    void poll();
    return () => {
      cancelled = true;
      if (timer !== undefined) window.clearTimeout(timer);
    };
  }, [cursor]);

  React.useEffect(() => {
    let cancelled = false;
    if (!online) {
      setRconReady(false);
      setRconStatusText("");
      return () => { cancelled = true; };
    }

    void serverApi.getRconStatus()
      .then((status) => {
        if (cancelled) return;
        setRconReady(status.ready);
        setRconStatusText(status.error || `${status.host}:${status.port}`);
      })
      .catch((reason) => {
        if (cancelled) return;
        setRconReady(false);
        setRconStatusText(reason instanceof Error ? reason.message : String(reason));
      });

    return () => { cancelled = true; };
  }, [online]);

  React.useEffect(() => {
    const viewport = viewportRef.current;
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [output]);

  async function sendCommand() {
    const value = command.trim();
    if (!value || sending || !online) return;
    setSending(true);
    try {
      const result = await serverApi.executeRconCommand(value);
      setRconReady(true);
      setRconStatusText(result.endpoint || "127.0.0.1");
      setOutput((current) =>
        `${current}\n> ${value}\n${result.response || "[OK]"}\n`.slice(-MAX_BUFFER),
      );
      setCommand("");
      setError(null);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : String(reason);
      setRconReady(false);
      setRconStatusText(message);
      setError(message);
    } finally {
      setSending(false);
    }
  }

  return (
    <Panel title={t("serverControl.liveConsole.title", { defaultValue: "Live Console" })}>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-parchment-300/60">
          <span className="flex items-center gap-2">
            <Terminal className="h-4 w-4" />
            {available
              ? t("serverControl.liveConsole.connected", { defaultValue: "Following ConanSandbox.log in real time." })
              : t("serverControl.liveConsole.waiting", { defaultValue: "Waiting for ConanSandbox.log..." })}
          </span>
          <span className={rconReady ? "text-emerald-300" : "text-blood-300"}>
            {rconReady
              ? t("serverControl.liveConsole.rconConfigured", { defaultValue: "RCON configured" })
              : t("serverControl.liveConsole.rconUnavailable", { defaultValue: "RCON unavailable" })}
            {rconStatusText ? ` · ${rconStatusText}` : ""}
          </span>
        </div>

        <pre
          ref={viewportRef}
          className="h-80 overflow-auto rounded-lg border border-parchment-500/15 bg-black/50 p-3 font-mono text-xs leading-5 text-parchment-200"
        >
          {output || t("serverControl.liveConsole.empty", { defaultValue: "No server output yet." })}
        </pre>

        {error && (
          <div className="rounded-md border border-blood-500/30 bg-blood-500/10 px-3 py-2 text-xs text-blood-300">
            {error}
          </div>
        )}

        <div className="flex gap-2">
          <input
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void sendCommand();
            }}
            disabled={!online || sending}
            placeholder={t("serverControl.liveConsole.commandPlaceholder", { defaultValue: "RCON command, e.g. ShowPlayers..." })}
            className="min-w-0 flex-1 rounded-md border border-parchment-500/20 bg-black/30 px-3 py-2 font-mono text-sm text-parchment-100 outline-none focus:border-mana-400/60 disabled:opacity-50"
          />
          <ActionButton
            variant="mana"
            icon={<Send />}
            onClick={() => void sendCommand()}
            disabled={!online || sending || !command.trim()}
          >
            {sending
              ? t("serverControl.liveConsole.sending", { defaultValue: "Sending..." })
              : t("serverControl.liveConsole.send", { defaultValue: "Send" })}
          </ActionButton>
          <ActionButton
            variant="ghost"
            icon={<Trash2 />}
            onClick={() => setOutput("")}
          >
            {t("serverControl.liveConsole.clear", { defaultValue: "Clear" })}
          </ActionButton>
        </div>

        <p className="text-[11px] text-parchment-300/45">
          {t("serverControl.liveConsole.security", {
            defaultValue: "RCON connects only to 127.0.0.1. The RCON password never reaches the browser.",
          })}
        </p>
      </div>
    </Panel>
  );
}

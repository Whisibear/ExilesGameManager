import * as React from "react";
import { serverApi } from "@/api";
import type { ServerStatus } from "@/types/models";
import PalworldMods from "@/pages/PalworldMods";
import ConanMods from "@/pages/ConanMods";

export default function Mods() {
  const [status, setStatus] = React.useState<ServerStatus | null>(null);
  const [loaded, setLoaded] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    serverApi
      .getServerStatus()
      .then((next) => {
        if (!cancelled) setStatus(next);
      })
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!loaded) {
    return <div className="p-6 text-sm text-parchment-300/60">Loading mod manager...</div>;
  }

  if (status?.gameId?.startsWith("conan_exiles")) {
    return <ConanMods />;
  }

  return <PalworldMods />;
}

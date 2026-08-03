import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface StatTileProps {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: "gold" | "mana" | "life" | "arcane" | "blood";
  className?: string;
  children?: ReactNode;
}

const ACCENT_STYLES: Record<string, string> = {
  gold: "text-gold-400 border-gold-600/20",
  mana: "text-mana-400 border-mana-600/20",
  life: "text-life-400 border-life-600/20",
  arcane: "text-arcane-400 border-arcane-600/20",
  blood: "text-blood-400 border-blood-600/20",
};

export function StatTile({ icon, label, value, hint, accent = "gold", className, children }: StatTileProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-stone-700/80 bg-gradient-to-br from-stone-800/88 to-abyss-950/88 p-4 shadow-[0_12px_32px_rgba(0,0,0,0.22)]",
        className
      )}
    >
      <div className="flex items-center gap-2.5">
        <span
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border bg-abyss-950/35 [&_svg]:h-4 [&_svg]:w-4",
            ACCENT_STYLES[accent]
          )}
        >
          {icon}
        </span>
        <p className="truncate text-[11px] font-semibold uppercase tracking-wider text-parchment-300/50">{label}</p>
      </div>
      <p className="mt-3 font-display text-2xl font-bold text-parchment-100">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-parchment-300/45">{hint}</p>}
      {children}
    </div>
  );
}

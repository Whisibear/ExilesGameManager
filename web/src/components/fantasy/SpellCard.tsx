import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

export type SpellCardStatus = "enabled" | "disabled" | "broken" | "neutral";
interface SpellCardProps { status?: SpellCardStatus; className?: string; children: React.ReactNode; draggable?: boolean; }
const STATUS_STYLES: Record<SpellCardStatus, string> = {
  enabled: "border-life-500/35 hover:border-life-400/55",
  disabled: "border-stone-700/80 opacity-75 grayscale-[0.35]",
  broken: "border-blood-500/45",
  neutral: "border-stone-700/80 hover:border-mana-500/38",
};

export function SpellCard({ status = "neutral", className, children, draggable }: SpellCardProps) {
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "group relative overflow-hidden rounded-xl border bg-gradient-to-br from-stone-800/88 via-abyss-900/92 to-abyss-950/88 p-5 shadow-[0_14px_36px_rgba(0,0,0,0.25)] transition-all hover:-translate-y-0.5",
        STATUS_STYLES[status],
        draggable && "cursor-grab active:cursor-grabbing",
        className
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-mana-400/35 to-transparent" />
      {status === "enabled" && <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_100%_0%,rgba(124,252,0,0.055),transparent_34%)]" />}
      {status === "broken" && <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_100%_0%,rgba(239,68,68,0.065),transparent_34%)]" />}
      <div className="relative">{children}</div>
    </motion.article>
  );
}

import * as React from "react";
import { cn } from "@/lib/utils";

interface ScrollPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  noPadding?: boolean;
}

export function ScrollPanel({ title, icon, actions, noPadding, className, children, ...props }: ScrollPanelProps) {
  return (
    <section
      className={cn(
        "group relative overflow-hidden rounded-xl border border-stone-700/80 bg-gradient-to-br from-stone-800/92 via-abyss-900/92 to-abyss-950/88 shadow-[0_18px_48px_rgba(0,0,0,0.28)] backdrop-blur-xl",
        className
      )}
      {...props}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-mana-400/70 to-transparent" />
      <div className="pointer-events-none absolute -right-16 -top-20 h-40 w-40 rounded-full bg-mana-400/[0.035] blur-3xl transition-opacity group-hover:opacity-100" />
      <div className="pointer-events-none absolute -bottom-20 -left-16 h-40 w-40 rounded-full bg-arcane-500/[0.025] blur-3xl" />

      {(title || actions) && (
        <header className="relative flex items-center justify-between gap-3 border-b border-stone-700/70 bg-abyss-950/28 px-5 py-4">
          <div className="flex min-w-0 items-center gap-3">
            {icon && (
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-mana-500/25 bg-mana-500/[0.07] text-mana-400 shadow-[0_0_18px_rgba(0,212,255,0.08)] [&_svg]:h-[17px] [&_svg]:w-[17px]">
                {icon}
              </span>
            )}
            {title && <h3 className="truncate font-display text-sm font-semibold uppercase tracking-[0.1em] text-parchment-100">{title}</h3>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cn("relative", !noPadding && "p-5")}>{children}</div>
    </section>
  );
}

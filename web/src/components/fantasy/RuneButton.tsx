import * as React from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const runeButtonVariants = cva(
  "relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-lg border font-body font-semibold tracking-wide transition-all disabled:pointer-events-none disabled:opacity-40 disabled:grayscale focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mana-400/35",
  {
    variants: {
      variant: {
        gold: "border-life-500/45 bg-life-500/[0.09] text-life-300 hover:border-life-400 hover:bg-life-500/[0.15]",
        arcane: "border-arcane-500/45 bg-arcane-500/[0.09] text-arcane-300 hover:border-arcane-400 hover:bg-arcane-500/[0.15]",
        mana: "border-mana-500/45 bg-mana-500/[0.09] text-mana-300 hover:border-mana-400 hover:bg-mana-500/[0.15]",
        life: "border-life-500/45 bg-life-500/[0.09] text-life-300 hover:border-life-400 hover:bg-life-500/[0.15]",
        danger: "border-blood-500/45 bg-blood-500/[0.09] text-blood-300 hover:border-blood-400 hover:bg-blood-500/[0.15]",
        ghost: "border-stone-700/90 bg-stone-900/30 text-parchment-300 hover:border-mana-500/45 hover:bg-mana-500/[0.06] hover:text-mana-300",
      },
      size: { sm: "h-8 px-3 text-xs", default: "h-10 px-4 text-sm", lg: "h-12 px-6 text-sm" },
    },
    defaultVariants: { variant: "gold", size: "default" },
  }
);

const glowByVariant: Record<string, string> = {
  gold: "hover:shadow-rune-life",
  arcane: "hover:shadow-[0_0_24px_rgba(139,92,246,0.16)]",
  mana: "hover:shadow-rune-mana",
  life: "hover:shadow-rune-life",
  danger: "hover:shadow-rune-blood",
  ghost: "",
};

export interface RuneButtonProps extends Omit<HTMLMotionProps<"button">, "children">, VariantProps<typeof runeButtonVariants> {
  icon?: React.ReactNode;
  children?: React.ReactNode;
  glowOnHover?: boolean;
}

export const RuneButton = React.forwardRef<HTMLButtonElement, RuneButtonProps>(
  ({ className, variant = "gold", size, icon, children, glowOnHover = true, ...props }, ref) => (
    <motion.button
      ref={ref}
      whileHover={{ y: props.disabled ? 0 : -1 }}
      whileTap={{ scale: props.disabled ? 1 : 0.985 }}
      className={cn(runeButtonVariants({ variant, size }), glowOnHover && glowByVariant[variant ?? "gold"], className)}
      {...props}
    >
      <span className="pointer-events-none absolute inset-x-3 top-0 h-px bg-gradient-to-r from-transparent via-current to-transparent opacity-50" />
      {icon && <span className="shrink-0 [&_svg]:h-4 [&_svg]:w-4">{icon}</span>}
      {children && <span>{children}</span>}
    </motion.button>
  )
);
RuneButton.displayName = "RuneButton";

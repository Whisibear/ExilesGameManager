import * as React from "react";
import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-stone-600/80 bg-abyss-950/55 px-3 py-2 text-sm text-parchment-100 placeholder:text-parchment-300/30 transition-colors",
          "focus-visible:outline-none focus-visible:border-mana-500/65 focus-visible:shadow-egm-cyan",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };

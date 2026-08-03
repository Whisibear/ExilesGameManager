import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-semibold transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mana-400/35",
  {
    variants: {
      variant: {
        default: "bg-stone-800/80 text-parchment-100 border border-stone-600/80 hover:border-mana-500/50 hover:bg-mana-500/[0.07]",
        ghost: "hover:bg-mana-500/[0.06] text-parchment-200 hover:text-mana-300",
        outline: "border border-stone-600/80 bg-transparent hover:border-mana-500/45 hover:bg-mana-500/[0.05] text-parchment-200",
        destructive:
          "bg-blood-600/20 text-blood-400 border border-blood-600/50 hover:bg-blood-600/30 hover:border-blood-500",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };

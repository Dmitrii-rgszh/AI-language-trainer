import type { ButtonHTMLAttributes, PropsWithChildren } from "react";
import { cn } from "../utils/cn";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const styles: Record<ButtonVariant, string> = {
  primary: "bg-accent text-white hover:bg-teal-700",
  secondary: "bg-sand text-ink hover:bg-[#ddccb6]",
  ghost: "bg-transparent text-ink hover:bg-white/60",
};

export function Button({
  children,
  className,
  variant = "primary",
  ...props
}: PropsWithChildren<ButtonProps>) {
  return (
    <button
      className={cn(
        "rounded-2xl px-4 py-2.5 text-sm font-semibold transition-colors disabled:opacity-50",
        styles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}


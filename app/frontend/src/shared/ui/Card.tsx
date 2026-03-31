import type { HTMLAttributes, PropsWithChildren } from "react";
import { cn } from "../utils/cn";

export function Card({
  children,
  className,
  ...props
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn("glass-panel rounded-[28px] border border-white/60 p-5 shadow-soft", className)}
      {...props}
    >
      {children}
    </div>
  );
}


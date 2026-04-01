import type { ElementType, PropsWithChildren } from "react";
import { cn } from "../../shared/utils/cn";

type LivingDepthSectionProps<T extends ElementType> = PropsWithChildren<{
  as?: T;
  id: string;
  fallback?: boolean;
  className?: string;
}>;

export function LivingDepthSection<T extends ElementType = "section">({
  as,
  children,
  className,
  fallback = false,
  id,
}: LivingDepthSectionProps<T>) {
  const Component = (as ?? "section") as ElementType;

  return (
    <Component
      data-living-depth-section={id}
      data-living-depth-fallback={fallback ? "true" : undefined}
      className={cn("living-depth-section", className)}
    >
      {children}
    </Component>
  );
}

import type { PropsWithChildren } from "react";

interface SectionHeadingProps {
  eyebrow?: string;
  title: string;
  description?: string;
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  children,
}: PropsWithChildren<SectionHeadingProps>) {
  return (
    <div className="flex flex-col gap-2">
      {eyebrow ? (
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{eyebrow}</div>
      ) : null}
      <div className="text-3xl font-semibold text-ink">{title}</div>
      {description ? <div className="max-w-2xl text-sm leading-6 text-slate-600">{description}</div> : null}
      {children}
    </div>
  );
}


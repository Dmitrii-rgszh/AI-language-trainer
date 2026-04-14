import { Card } from "../../shared/ui/Card";
import { cn } from "../../shared/utils/cn";

type LizaGuidanceGridProps = {
  className?: string;
  currentLabel: string;
  currentText: string;
  whyLabel: string;
  whyText: string;
  nextLabel: string;
  nextText: string;
};

const toneClassNames = [
  "border-coral/14 bg-white/78",
  "border-accent/14 bg-accent/5",
  "border-sand-dark/14 bg-sand/75",
];

export function LizaGuidanceGrid({
  className,
  currentLabel,
  currentText,
  whyLabel,
  whyText,
  nextLabel,
  nextText,
}: LizaGuidanceGridProps) {
  const items = [
    { id: "current", label: currentLabel, text: currentText },
    { id: "why", label: whyLabel, text: whyText },
    { id: "next", label: nextLabel, text: nextText },
  ];

  return (
    <div className={cn("grid gap-4 xl:grid-cols-3", className)}>
      {items.map((item, index) => (
        <Card key={item.id} className={cn("space-y-3 border", toneClassNames[index] ?? toneClassNames[0])}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{item.label}</div>
          <div className="text-sm leading-6 text-slate-700">{item.text}</div>
        </Card>
      ))}
    </div>
  );
}

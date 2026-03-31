import type { LessonBlock } from "../../entities/lesson/model";
import { useLocale } from "../i18n/useLocale";
import { cn } from "../utils/cn";

interface LessonStepperProps {
  blocks: LessonBlock[];
  activeIndex: number;
}

export function LessonStepper({ blocks, activeIndex }: LessonStepperProps) {
  const { tr } = useLocale();

  return (
    <div className="grid gap-3 md:grid-cols-5">
      {blocks.map((block, index) => (
        <div
          key={block.id}
          className={cn(
            "rounded-2xl border border-white/70 px-3 py-3 text-sm",
            index === activeIndex ? "bg-accent text-white" : "bg-white/70 text-slate-700",
          )}
        >
          <div className="text-xs uppercase tracking-[0.16em] opacity-80">
            {tr("Step")} {index + 1}
          </div>
          <div className="mt-1 font-medium">{block.title}</div>
        </div>
      ))}
    </div>
  );
}

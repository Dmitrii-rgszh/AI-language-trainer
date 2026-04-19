import type { DailyLoopPlan } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type DailyRitualPanelProps = {
  plan: DailyLoopPlan;
  tr: (value: string) => string;
};

export function DailyRitualPanel({ plan, tr }: DailyRitualPanelProps) {
  const ritual = plan.ritual;

  if (!ritual) {
    return null;
  }

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">
            {tr("Daily ritual")}
          </div>
          <div className="mt-2 text-2xl font-semibold text-ink">{ritual.headline}</div>
          <div className="mt-2 text-sm leading-6 text-slate-600">{ritual.promise}</div>
        </div>
        <div className="rounded-2xl bg-sand/80 px-4 py-2 text-sm font-semibold text-ink">
          {plan.estimatedMinutes} {tr("minutes")}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Completion rule")}:</span> {ritual.completionRule}
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Closure rule")}:</span> {ritual.closureRule}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {ritual.stages.map((stage, index) => (
          <div key={stage.id} className="rounded-2xl border border-white/70 bg-white/78 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-ink">{`${index + 1}. ${stage.title}`}</div>
              <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
                {stage.emphasis}
              </div>
            </div>
            <div className="mt-3 text-sm leading-6 text-slate-700">{stage.summary}</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

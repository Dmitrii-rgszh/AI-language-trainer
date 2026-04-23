import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type DashboardDailyLoopSectionProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  showActions?: boolean;
  tr: (value: string) => string;
};

export function DashboardDailyLoopSection({
  dailyLoopPlan,
  journeyState,
  showActions = false,
  tr,
}: DashboardDailyLoopSectionProps) {
  if (!dailyLoopPlan) {
    return null;
  }

  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape = describeRouteDayShape(dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr);
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const compactSummary =
    dailyLoopPlan.summary.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 1).join(" ") || dailyLoopPlan.summary;

  return (
    <Card className="space-y-4">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-coral">{tr("Plan for today")}</div>
        <div className="mt-2 text-2xl font-semibold text-ink">{dailyLoopPlan.headline}</div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-700">
        <div className="rounded-full border border-white/70 bg-white/76 px-3 py-1">
          {tr("Focus")}: {tr(dailyLoopPlan.focusArea)}
        </div>
        <div className="rounded-full border border-white/70 bg-white/76 px-3 py-1">
          {dailyLoopPlan.estimatedMinutes} {tr("min")}
        </div>
        <div className="rounded-full border border-white/70 bg-white/76 px-3 py-1">
          {dayShape.title}
        </div>
      </div>

      <div className="rounded-[24px] bg-sand/70 p-4 text-sm leading-6 text-slate-700">
        {compactSummary}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {dailyLoopPlan.steps.slice(0, 2).map((step) => (
          <div key={step.id} className="rounded-[22px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{tr(step.skill)}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{tr(step.title)}</div>
            <div className="mt-2 text-sm leading-6 text-slate-700">{step.description}</div>
          </div>
        ))}
      </div>

      {dailyLoopPlan.completedAt && tomorrowPreview ? (
        <div className="rounded-[22px] border border-accent/20 bg-accent/8 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("What happens after this")}:</span> {tomorrowPreview.headline}
          {practiceShiftLine ? ` ${practiceShiftLine}` : ""}
        </div>
      ) : null}

      {showActions ? (
        <div className="flex flex-wrap gap-3">
          <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
            {tr("Open route preview")}
          </Link>
        </div>
      ) : null}
    </Card>
  );
}

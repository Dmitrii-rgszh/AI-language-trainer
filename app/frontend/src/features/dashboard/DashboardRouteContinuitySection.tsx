import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { JourneySessionSummaryPanel } from "../../widgets/journey/JourneySessionSummaryPanel";

type DashboardRouteContinuitySectionProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  onStartDailyLoop: () => Promise<void>;
  tr: (value: string) => string;
};

export function DashboardRouteContinuitySection({
  dailyLoopPlan,
  journeyState,
  onStartDailyLoop,
  tr,
}: DashboardRouteContinuitySectionProps) {
  if (!dailyLoopPlan) {
    return null;
  }

  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const hasCompletedToday = dailyLoopPlan.completedAt !== null;
  const hasStartedToday = dailyLoopPlan.lessonRunId !== null;

  if (hasCompletedToday && tomorrowPreview) {
    return (
      <Card className="space-y-4 border border-accent/20 bg-accent/6">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">{tr("Route continuity")}</div>
        <div className="text-2xl font-semibold text-ink">{tr("Today's route is complete")}</div>
        <div className="rounded-[22px] bg-white/78 p-4 text-sm leading-6 text-slate-700">
          {journeyState?.currentStrategySummary ?? tr("The system has already updated the route from today's session.")}
        </div>
        {sessionSummary ? (
          <JourneySessionSummaryPanel
            summary={sessionSummary}
            title={tr("Today's session shift")}
            tr={tr}
          />
        ) : null}
        <div className="rounded-[22px] border border-white/70 bg-white/84 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-coral">{tr("Tomorrow preview")}</div>
          <div className="mt-2 text-lg font-semibold text-ink">{tomorrowPreview.headline}</div>
          <div className="mt-3 text-sm leading-6 text-slate-700">{tomorrowPreview.reason}</div>
          {practiceShiftLine ? (
            <div className="mt-3 rounded-[18px] bg-accent/8 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">{tr("Practice shift")}:</span> {practiceShiftLine}
            </div>
          ) : null}
          <div className="mt-3 rounded-[18px] bg-sand/70 p-3 text-sm text-slate-700">
            {tomorrowPreview.nextStepHint}
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to={routes.progress} className="proof-lesson-primary-button">
            {tr("Review updated progress")}
          </Link>
          <Link to={routes.activity} className="proof-lesson-secondary-action">
            {tr("Open activity trail")}
          </Link>
        </div>
      </Card>
    );
  }

  if (!hasStartedToday) {
    return (
      <Card className="space-y-4">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("Route continuity")}</div>
        <div className="text-2xl font-semibold text-ink">{tr("Today's route is waiting for you")}</div>
        <div className="rounded-[22px] bg-white/78 p-4 text-sm leading-6 text-slate-700">
          {journeyState?.nextBestAction ?? dailyLoopPlan.nextStepHint}
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Focus")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{dailyLoopPlan.focusArea}</div>
          </div>
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Session")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{dailyLoopPlan.recommendedLessonTitle}</div>
          </div>
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Budget")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{dailyLoopPlan.estimatedMinutes} {tr("min")}</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="button" onClick={() => void onStartDailyLoop()}>
            {tr("Start today's route")}
          </Button>
          <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
            {tr("Review the route")}
          </Link>
        </div>
      </Card>
    );
  }

  return null;
}

import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { buildRouteFollowUpHintFromState } from "../../shared/journey/route-entry-orchestration";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { JourneySessionSummaryPanel } from "../../widgets/journey/JourneySessionSummaryPanel";

type DashboardRouteContinuitySectionProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  onStartDailyLoop: () => Promise<void>;
  showActions?: boolean;
  tr: (value: string) => string;
};

export function DashboardRouteContinuitySection({
  dailyLoopPlan,
  journeyState,
  onStartDailyLoop,
  showActions = true,
  tr,
}: DashboardRouteContinuitySectionProps) {
  if (!dailyLoopPlan) {
    return null;
  }

  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const routeFollowUpMemory = journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  const dayShape = describeRouteDayShape(dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr);
  const followUpHint = buildRouteFollowUpHintFromState(dailyLoopPlan, journeyState, tr);
  const hasDistinctCarry =
    routeFollowUpMemory?.carryLabel &&
    routeFollowUpMemory.carryLabel !== routeFollowUpMemory.currentLabel &&
    routeFollowUpMemory.carryLabel !== routeFollowUpMemory.followUpLabel;
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const hasCompletedToday = dailyLoopPlan.completedAt !== null;
  const hasStartedToday = dailyLoopPlan.lessonRunId !== null;
  const waitingDescription = dayShape
    ? `${tr("Finish today's loop to unlock the next focused step around")} ${tr(dailyLoopPlan.focusArea)}.`
    : tr("Finish today's loop to unlock the next focused step.");
  const nextAfterThis =
    followUpHint ??
    dailyLoopPlan.nextStepHint ??
    tr("After this, I will show the next focused step.");

  if (hasCompletedToday && tomorrowPreview) {
    return (
      <Card className="space-y-4 border border-accent/20 bg-accent/6">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-accent">{tr("Route continuity")}</div>
        <div className="text-2xl font-semibold text-ink">{tr("Today's route is complete")}</div>
        <div className="rounded-[22px] bg-white/78 p-4 text-sm leading-6 text-slate-700">
          {journeyState?.currentStrategySummary ?? tr("The system has already updated the route from today's session.")}
        </div>
        {routeRecoveryMemory ? (
          <div className="rounded-[22px] bg-white/78 p-4 text-sm leading-6 text-slate-700">
            <span className="font-semibold text-ink">{tr("Recovery arc")}:</span> {routeRecoveryMemory.summary}
          </div>
        ) : null}
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
            {tr("Review the updated route")}
          </Link>
          <Link to={routes.activity} className="proof-lesson-secondary-action">
            {tr("Open the route trail")}
          </Link>
        </div>
      </Card>
    );
  }

  if (!hasStartedToday) {
    return (
      <Card className="space-y-4">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("Next step")}</div>
        <div className="text-2xl font-semibold text-ink">{tr("Today we focus on")} {tr(dailyLoopPlan.focusArea)}.</div>
        <div className="rounded-[22px] bg-white/78 p-4 text-sm leading-6 text-slate-700">{waitingDescription}</div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Focus")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{tr(dailyLoopPlan.focusArea)}</div>
          </div>
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Budget")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{dailyLoopPlan.estimatedMinutes} {tr("min")}</div>
          </div>
          <div className="rounded-[20px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("After this")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{nextAfterThis}</div>
          </div>
        </div>
        {dayShape ? (
          <div className="flex flex-wrap gap-2 text-xs font-semibold text-slate-600">
            <div className="rounded-full bg-accent/10 px-3 py-1 text-accent">{dayShape.title}</div>
            <div className="rounded-full bg-white px-3 py-1">{dayShape.compactnessLabel}</div>
            {routeRecoveryMemory ? (
              <div className="rounded-full bg-white px-3 py-1">
                {tr(routeRecoveryMemory.phase)}
                {routeRecoveryMemory.focusSkill ? ` · ${tr(routeRecoveryMemory.focusSkill)}` : ""}
              </div>
            ) : null}
            {hasDistinctCarry ? (
              <div className="rounded-full bg-sand/70 px-3 py-1">
                {tr("Then")}: {routeFollowUpMemory?.carryLabel}
              </div>
            ) : null}
          </div>
        ) : null}
        {showActions ? (
          <div className="flex flex-wrap gap-3">
            <Button type="button" onClick={() => void onStartDailyLoop()}>
              {tr("Start today's route")}
            </Button>
            <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
              {tr("Open route preview")}
            </Link>
          </div>
        ) : null}
      </Card>
    );
  }

  return null;
}

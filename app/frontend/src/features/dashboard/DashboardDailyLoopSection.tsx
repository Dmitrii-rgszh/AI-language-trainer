import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { resolveTaskDrivenInputSurface } from "../../shared/journey/task-driven-input";
import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { DailyRitualPanel } from "../../widgets/journey/DailyRitualPanel";

type DashboardDailyLoopSectionProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  onStartDailyLoop: () => Promise<void>;
  tr: (value: string) => string;
};

export function DashboardDailyLoopSection({
  dailyLoopPlan,
  journeyState,
  onStartDailyLoop,
  tr,
}: DashboardDailyLoopSectionProps) {
  if (!dailyLoopPlan) {
    return null;
  }

  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const skillTrajectory = journeyState?.strategySnapshot.skillTrajectory ?? null;
  const strategyMemory = journeyState?.strategySnapshot.strategyMemory ?? null;
  const routeCadenceMemory = journeyState?.strategySnapshot.routeCadenceMemory ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape = describeRouteDayShape(dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr);
  const taskDrivenInput = resolveTaskDrivenInputSurface(dailyLoopPlan, journeyState, tr);
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const tomorrowSignals = [
    tomorrowPreview?.carryOverSignalLabel
      ? `${tr("Carry forward")}: ${tomorrowPreview.carryOverSignalLabel}`
      : null,
    tomorrowPreview?.watchSignalLabel
      ? `${tr("Watch next")}: ${tomorrowPreview.watchSignalLabel}`
      : null,
    skillTrajectory?.focusSkill
      ? `${tr("Multi-day memory")}: ${skillTrajectory.focusSkill} ${skillTrajectory.direction}`
      : null,
    strategyMemory?.focusSkill
      ? `${tr("Long memory")}: ${strategyMemory.focusSkill} ${strategyMemory.persistenceLevel}`
      : null,
    dayShape?.title
      ? `${tr("Day shape")}: ${dayShape.title}`
      : null,
    dayShape?.expansionStageLabel
      ? `${tr("Expansion stage")}: ${dayShape.expansionStageLabel}`
      : null,
    routeRecoveryMemory?.phase
      ? `${tr("Recovery arc")}: ${routeRecoveryMemory.phase}`
      : null,
  ].filter((item): item is string => Boolean(item));

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-coral">{tr("Daily Loop")}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{dailyLoopPlan.headline}</div>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <div className="rounded-full border border-white/70 bg-white/76 px-3 py-1 text-xs font-semibold text-slate-700">
            {dayShape.title}
          </div>
          <div className="rounded-[22px] bg-white/72 px-4 py-3 text-sm text-slate-700">
            {`${dailyLoopPlan.estimatedMinutes} ${tr("minutes")}`}
          </div>
        </div>
      </div>

      <div className="rounded-[24px] bg-sand/70 p-4 text-sm leading-6 text-slate-700">
        {dailyLoopPlan.summary}
      </div>

      <div className="rounded-[24px] border border-white/70 bg-white/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{tr("Day shape")}</div>
            <div className="mt-2 text-lg font-semibold text-ink">{dayShape.title}</div>
          </div>
          <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
            {dayShape.compactnessLabel}
          </div>
        </div>
        <div className="mt-3 text-sm leading-6 text-slate-700">{dayShape.summary}</div>
        {dayShape.expansionStageLabel ? (
          <div className="mt-3 rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent inline-flex">
            {dayShape.expansionStageLabel}
          </div>
        ) : null}
        {dayShape.expansionWindowLabel ? (
          <div className="mt-3 text-xs text-slate-500">{dayShape.expansionWindowLabel}</div>
        ) : null}
      </div>

      {skillTrajectory ? (
        <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Multi-day memory")}:</span> {skillTrajectory.summary}
        </div>
      ) : null}
      {strategyMemory ? (
        <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Long strategy memory")}:</span> {strategyMemory.summary}
        </div>
      ) : null}
      {routeCadenceMemory ? (
        <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Route cadence")}:</span> {routeCadenceMemory.summary}
        </div>
      ) : null}
      {routeRecoveryMemory ? (
        <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Recovery arc")}:</span> {routeRecoveryMemory.summary}
        </div>
      ) : null}

      {dailyLoopPlan.completedAt && tomorrowPreview ? (
        <div className="rounded-[24px] border border-accent/20 bg-accent/8 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Tomorrow preview")}</div>
          <div className="mt-2 text-lg font-semibold text-ink">{tomorrowPreview.headline}</div>
          <div className="mt-3 text-sm leading-6 text-slate-700">{tomorrowPreview.reason}</div>
          {practiceShiftLine ? (
            <div className="mt-3 rounded-[18px] bg-white/72 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">{tr("Practice shift")}:</span> {practiceShiftLine}
            </div>
          ) : null}
          {tomorrowSignals.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {tomorrowSignals.map((signal) => (
                <div
                  key={signal}
                  className="rounded-full border border-white/70 bg-white/74 px-3 py-1 text-xs font-semibold text-slate-700"
                >
                  {signal}
                </div>
              ))}
            </div>
          ) : null}
          <div className="mt-3 rounded-[18px] bg-white/70 p-3 text-sm text-slate-700">
            {tomorrowPreview.nextStepHint}
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-3">
        {dailyLoopPlan.steps.slice(0, 3).map((step) => (
          <div key={step.id} className="rounded-[22px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{step.skill}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{step.title}</div>
            <div className="mt-2 text-sm leading-6 text-slate-700">{step.description}</div>
          </div>
        ))}
      </div>

      {taskDrivenInput ? (
        <div className="rounded-[24px] border border-accent/15 bg-accent/8 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Task-driven input")}</div>
          <div className="mt-2 text-lg font-semibold text-ink">{taskDrivenInput.title}</div>
          <div className="mt-3 text-sm leading-6 text-slate-700">{taskDrivenInput.summary}</div>
          <div className="mt-3 rounded-[18px] bg-white/76 p-3 text-sm text-slate-700">{taskDrivenInput.bridge}</div>
          <div className="mt-3 flex flex-wrap gap-3">
            <Link to={taskDrivenInput.route} className="proof-lesson-primary-button">
              {taskDrivenInput.title}
            </Link>
            <Link to={routes.lessonRunner} className="proof-lesson-secondary-action">
              {tr("Open guided route directly")}
            </Link>
          </div>
        </div>
      ) : null}

      {dailyLoopPlan.ritual ? <DailyRitualPanel plan={dailyLoopPlan} tr={tr} /> : null}

      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={() => void onStartDailyLoop()} disabled={dailyLoopPlan.completedAt !== null}>
          {dailyLoopPlan.lessonRunId ? tr("Resume today’s route") : tr("Start today’s route")}
        </Button>
        <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
          {tr("Open route preview")}
        </Link>
      </div>
    </Card>
  );
}

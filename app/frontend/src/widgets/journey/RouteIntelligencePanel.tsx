import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type RouteIntelligencePanelProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  title: string;
  tr: (value: string) => string;
};

export function RouteIntelligencePanel({
  dailyLoopPlan,
  journeyState,
  title,
  tr,
}: RouteIntelligencePanelProps) {
  if (!journeyState) {
    return null;
  }

  const snapshot = journeyState.strategySnapshot;
  const sessionSummary = snapshot.sessionSummary ?? null;
  const tomorrowPreview = snapshot.tomorrowPreview ?? null;
  const activePlanSeed = snapshot.activePlanSeed ?? null;
  const skillTrajectory = snapshot.skillTrajectory ?? null;
  const practiceShift = sessionSummary?.practiceMixEvaluation ?? null;

  const routeSignals = [
    sessionSummary?.carryOverSignalLabel
      ? `${tr("Carry forward")}: ${sessionSummary.carryOverSignalLabel}`
      : null,
    sessionSummary?.watchSignalLabel
      ? `${tr("Watch next")}: ${sessionSummary.watchSignalLabel}`
      : null,
    dailyLoopPlan?.focusArea
      ? `${tr("Current focus")}: ${dailyLoopPlan.focusArea}`
      : null,
    activePlanSeed?.source
      ? `${tr("Route seed")}: ${activePlanSeed.source}`
      : null,
    practiceShift?.leadPracticeTitle
      ? `${tr("Lead practice")}: ${practiceShift.leadPracticeTitle}`
      : null,
    skillTrajectory?.focusSkill
      ? `${tr("Multi-day memory")}: ${skillTrajectory.focusSkill} ${skillTrajectory.direction}`
      : null,
  ].filter((item): item is string => Boolean(item));

  const routeStory =
    practiceShift?.summaryLine ||
    journeyState.currentStrategySummary ||
    sessionSummary?.strategyShift ||
    tomorrowPreview?.reason ||
    dailyLoopPlan?.whyThisNow ||
    "";

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{title}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{tr("Why the route looks like this")}</div>
        </div>
        {journeyState.stage ? (
          <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
            {journeyState.stage}
          </div>
        ) : null}
      </div>

      <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
        {routeStory}
      </div>

      {routeSignals.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {routeSignals.map((signal) => (
            <div
              key={signal}
              className="rounded-full border border-white/70 bg-sand/70 px-3 py-1 text-xs font-semibold text-slate-700"
            >
              {signal}
            </div>
          ))}
        </div>
      ) : null}

      <div className={`grid gap-3 ${skillTrajectory ? "md:grid-cols-4" : "md:grid-cols-3"}`}>
        <div className="rounded-[20px] bg-sand/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Current route")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {dailyLoopPlan?.recommendedLessonTitle ?? tr("Guided route")}
          </div>
          <div className="mt-2 text-sm text-slate-600">
            {dailyLoopPlan?.summary ?? journeyState.nextBestAction}
          </div>
        </div>

        <div className="rounded-[20px] bg-white/82 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("What carries forward")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {sessionSummary?.carryOverSignalLabel ?? tr("Main signal")}
          </div>
          <div className="mt-2 text-sm text-slate-600">
            {sessionSummary?.whatWorked ?? tr("The route carries the strongest recent signal into the next session.")}
          </div>
        </div>

        <div className="rounded-[20px] bg-white/82 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("What is being watched")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {sessionSummary?.watchSignalLabel ?? tr("Weak signal")}
          </div>
          <div className="mt-2 text-sm text-slate-600">
            {sessionSummary?.watchSignal ?? tomorrowPreview?.reason ?? tr("The route still protects one weaker signal while it moves forward.")}
          </div>
        </div>

        {skillTrajectory ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Multi-day memory")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {skillTrajectory.focusSkill} · {skillTrajectory.direction}
            </div>
            <div className="mt-2 text-sm text-slate-600">{skillTrajectory.summary}</div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

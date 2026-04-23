import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { buildRouteFollowUpHintFromState } from "../../shared/journey/route-entry-orchestration";
import { describeRitualWindow } from "../../shared/journey/ritual-window";
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
  const strategyMemory = snapshot.strategyMemory ?? null;
  const routeCadenceMemory = snapshot.routeCadenceMemory ?? null;
  const routeRecoveryMemory = snapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = snapshot.routeReentryProgress ?? null;
  const routeEntryMemory = snapshot.routeEntryMemory ?? null;
  const ritualSignalMemory = snapshot.ritualSignalMemory ?? null;
  const dayShape = dailyLoopPlan
    ? describeRouteDayShape(dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr)
    : null;
  const ritualWindow = describeRitualWindow(ritualSignalMemory, tr);
  const routeFollowUpMemory = snapshot.routeFollowUpMemory ?? null;
  const practiceShift = sessionSummary?.practiceMixEvaluation ?? null;
  const routeReentryLabel = routeReentryProgress?.nextRoute
    ? {
        "/grammar": tr("grammar support"),
        "/vocabulary": tr("vocabulary support"),
        "/speaking": tr("speaking support"),
        "/pronunciation": tr("pronunciation support"),
        "/writing": tr("writing support"),
        "/profession": tr("professional support"),
      }[routeReentryProgress.nextRoute] ?? routeReentryProgress.nextRoute
    : null;
  const routeEntryResetLabel =
    routeEntryMemory?.activeNextRoute && (routeEntryMemory.activeNextRouteVisits ?? 0) >= 2
      ? {
          "/grammar": tr("grammar support"),
          "/vocabulary": tr("vocabulary support"),
          "/speaking": tr("speaking support"),
          "/pronunciation": tr("pronunciation support"),
          "/writing": tr("writing support"),
          "/profession": tr("professional support"),
        }[routeEntryMemory.activeNextRoute] ?? routeEntryMemory.activeNextRoute
      : null;
  const routeEntryReleaseLabel =
    routeEntryMemory?.activeNextRoute && routeEntryMemory.readyToReopenActiveNextRoute
      ? {
          "/grammar": tr("grammar support"),
          "/vocabulary": tr("vocabulary support"),
          "/speaking": tr("speaking support"),
          "/pronunciation": tr("pronunciation support"),
          "/writing": tr("writing support"),
          "/profession": tr("professional support"),
        }[routeEntryMemory.activeNextRoute] ?? routeEntryMemory.activeNextRoute
      : null;
  const followUpHint = buildRouteFollowUpHintFromState(dailyLoopPlan, journeyState, tr);

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
    strategyMemory?.focusSkill
      ? `${tr("Long memory")}: ${strategyMemory.focusSkill} ${strategyMemory.persistenceLevel}`
      : null,
    dayShape?.title
      ? `${tr("Day shape")}: ${dayShape.title}`
      : null,
    dayShape?.substageLabel
      ? `${tr("Reopen stage")}: ${dayShape.substageLabel}`
      : null,
    dayShape?.expansionStageLabel
      ? `${tr("Expansion stage")}: ${dayShape.expansionStageLabel}`
      : null,
    dayShape?.expansionWindowLabel
      ? `${tr("Expansion window")}: ${dayShape.expansionWindowLabel}`
      : null,
    routeCadenceMemory?.status
      ? `${tr("Route cadence")}: ${routeCadenceMemory.status}`
      : null,
    routeRecoveryMemory?.phase
      ? `${tr("Recovery arc")}: ${routeRecoveryMemory.phase}`
      : null,
    ritualWindow?.title
      ? `${tr("Ritual arc")}: ${ritualWindow.title}`
      : null,
    routeEntryResetLabel
      ? `${tr("Reset target")}: ${routeEntryResetLabel}`
      : null,
    routeEntryReleaseLabel
      ? `${tr("Ready to reopen")}: ${routeEntryReleaseLabel}`
      : null,
    routeReentryLabel
      ? `${tr("Next support step")}: ${routeReentryLabel}`
      : null,
    followUpHint
      ? `${tr("What comes next")}: ${followUpHint}`
      : null,
    routeFollowUpMemory?.carryLabel
      ? `${tr("Carry forward")}: ${routeFollowUpMemory.carryLabel}`
      : null,
  ].filter((item): item is string => Boolean(item));

  const routeStory =
    practiceShift?.summaryLine ||
    journeyState.currentStrategySummary ||
    sessionSummary?.strategyShift ||
    tomorrowPreview?.reason ||
    dailyLoopPlan?.whyThisNow ||
    "";
  const intelligenceCardCount =
    3 +
    (skillTrajectory ? 1 : 0) +
    (strategyMemory ? 1 : 0) +
    (dayShape ? 1 : 0) +
    (ritualWindow ? 1 : 0) +
    (routeCadenceMemory ? 1 : 0) +
    (routeRecoveryMemory ? 1 : 0) +
    (routeEntryResetLabel ? 1 : 0) +
    (routeEntryReleaseLabel ? 1 : 0) +
    (routeReentryLabel ? 1 : 0);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{title}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{tr("Why Liza shaped the route this way")}</div>
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

      <div
        className={`grid gap-3 ${
          intelligenceCardCount >= 5
            ? "xl:grid-cols-5 md:grid-cols-3"
            : intelligenceCardCount === 4
              ? "md:grid-cols-4"
              : "md:grid-cols-3"
        }`}
      >
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
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Trajectory memory")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {skillTrajectory.focusSkill} · {skillTrajectory.direction}
            </div>
            <div className="mt-2 text-sm text-slate-600">{skillTrajectory.summary}</div>
          </div>
        ) : null}

        {strategyMemory ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Long strategy memory")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {strategyMemory.focusSkill} · {strategyMemory.persistenceLevel}
            </div>
            <div className="mt-2 text-sm text-slate-600">{strategyMemory.summary}</div>
          </div>
        ) : null}

        {dayShape ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Day shape")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {dayShape.title} · {dayShape.compactnessLabel}
            </div>
            {dayShape.substageLabel ? (
              <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                {dayShape.substageLabel}
              </div>
            ) : null}
            {dayShape.expansionStageLabel ? (
              <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent">
                {dayShape.expansionStageLabel}
              </div>
            ) : null}
            {dayShape.expansionWindowLabel ? (
              <div className="mt-2 text-xs text-slate-500">{dayShape.expansionWindowLabel}</div>
            ) : null}
            <div className="mt-2 text-sm text-slate-600">{dayShape.summary}</div>
          </div>
        ) : null}

        {ritualWindow ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Ritual arc")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{ritualWindow.title}</div>
            {ritualWindow.windowLabel ? (
              <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                {ritualWindow.windowLabel}
              </div>
            ) : null}
            <div className="mt-2 text-sm text-slate-600">{ritualWindow.summary}</div>
            {ritualWindow.hint ? (
              <div className="mt-2 text-sm text-slate-500">{ritualWindow.hint}</div>
            ) : null}
          </div>
        ) : null}

        {routeCadenceMemory ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Route cadence")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {routeCadenceMemory.status}
            </div>
            <div className="mt-2 text-sm text-slate-600">{routeCadenceMemory.summary}</div>
          </div>
        ) : null}

        {routeRecoveryMemory ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Recovery arc")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {routeRecoveryMemory.phase}
              {routeRecoveryMemory.focusSkill ? ` · ${routeRecoveryMemory.focusSkill}` : ""}
            </div>
            <div className="mt-2 text-sm text-slate-600">{routeRecoveryMemory.summary}</div>
          </div>
        ) : null}

        {followUpHint ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("What comes next")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{tr("Next guided step")}</div>
            <div className="mt-2 text-sm text-slate-600">{followUpHint}</div>
          </div>
        ) : null}

        {routeFollowUpMemory?.summary || routeFollowUpMemory?.currentLabel || routeFollowUpMemory?.followUpLabel || routeFollowUpMemory?.carryLabel ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Route flow")}</div>
            <div className="mt-2 flex flex-wrap gap-2 text-xs font-semibold text-slate-700">
              {routeFollowUpMemory?.currentLabel ? (
                <div className="rounded-full bg-accent/10 px-3 py-1">
                  {tr("Now")}: {routeFollowUpMemory.currentLabel}
                </div>
              ) : null}
              {routeFollowUpMemory?.followUpLabel ? (
                <div className="rounded-full bg-sand/70 px-3 py-1">
                  {tr("Then")}: {routeFollowUpMemory.followUpLabel}
                </div>
              ) : null}
              {routeFollowUpMemory?.carryLabel &&
              routeFollowUpMemory.carryLabel !== routeFollowUpMemory.currentLabel &&
              routeFollowUpMemory.carryLabel !== routeFollowUpMemory.followUpLabel ? (
                <div className="rounded-full bg-white px-3 py-1">
                  {tr("Carry")}: {routeFollowUpMemory.carryLabel}
                </div>
              ) : null}
            </div>
            {routeFollowUpMemory?.summary ? (
              <div className="mt-3 text-sm text-slate-600">{routeFollowUpMemory.summary}</div>
            ) : null}
          </div>
        ) : null}

        {routeEntryResetLabel ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Connected reset")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{routeEntryResetLabel}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("The route is temporarily reconnecting through the main path before this support surface opens again.")}
            </div>
          </div>
        ) : null}

        {routeEntryReleaseLabel ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Support ready to reopen")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{routeEntryReleaseLabel}</div>
            {dayShape?.substageLabel ? (
              <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                {dayShape.substageLabel}
              </div>
            ) : null}
            <div className="mt-2 text-sm text-slate-600">
              {tr("The calmer reset has done its job, so this support surface can come back into the connected route now.")}
            </div>
          </div>
        ) : null}

        {routeReentryLabel && !routeEntryResetLabel && !routeEntryReleaseLabel ? (
          <div className="rounded-[20px] bg-white/82 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Re-entry sequence")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {routeReentryLabel}
              {Array.isArray(routeReentryProgress?.completedRoutes) &&
              Array.isArray(routeReentryProgress?.orderedRoutes)
                ? ` · ${routeReentryProgress.completedRoutes.length}/${routeReentryProgress.orderedRoutes.length}`
                : ""}
            </div>
            <div className="mt-2 text-sm text-slate-600">
              {journeyState.nextBestAction}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

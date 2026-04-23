import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { buildRouteFollowUpHint } from "../../shared/journey/route-entry-orchestration";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import {
  readDismissedJourneyReentryKey,
  writeDismissedJourneyReentryKey,
} from "../../shared/journey/reentry-prompt";
import type { DashboardData } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";

type JourneyReentryPromptProps = {
  dashboard: DashboardData | null;
  pathname: string;
  onOpenDashboard: () => void;
  onResumeRoute: () => Promise<void>;
  onStartTodayRoute: () => Promise<void>;
  tr: (value: string) => string;
};

type ReentryPromptModel = {
  id: string;
  title: string;
  description: string;
  detail: string;
  carryDetail?: string;
  primaryActionKind: "resume" | "start" | "open_dashboard";
  primaryLabel: string;
  secondaryHref: string;
  secondaryLabel: string;
  toneClassName: string;
};

const hiddenPaths = new Set<string>([
  routes.dashboard,
  routes.dailyLoop,
  routes.lessonRunner,
  routes.lessonResults,
  routes.welcome,
  routes.welcomeClassic,
  routes.onboarding,
  routes.liveAvatar,
]);

function buildPromptModel(dashboard: DashboardData, tr: (value: string) => string): ReentryPromptModel | null {
  const journeyState = dashboard.journeyState;
  const dailyLoopPlan = dashboard.dailyLoopPlan;
  const resumeLesson = dashboard.resumeLesson;
  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const skillTrajectory = journeyState?.strategySnapshot.skillTrajectory ?? null;
  const strategyMemory = journeyState?.strategySnapshot.strategyMemory ?? null;
  const routeCadenceMemory = journeyState?.strategySnapshot.routeCadenceMemory ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape = dailyLoopPlan
    ? describeRouteDayShape(dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr)
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
  const routeFollowUpMemory = journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  const followUpHint = buildRouteFollowUpHint(dashboard, tr);

  if (resumeLesson) {
    return {
      id: `resume:${resumeLesson.runId}:${journeyState?.updatedAt ?? "stable"}`,
      title: tr("Your route is already in progress"),
      description: tr("You already have an active guided session. The strongest move right now is to return to it, not switch into a new module."),
      detail:
        `${tr("Current block")}: ${tr(resumeLesson.currentBlockTitle)}. ${tr("Progress")}: ${resumeLesson.completedBlocks}/${resumeLesson.totalBlocks}.` +
        (dayShape ? ` ${tr("Day shape")}: ${dayShape.title} · ${dayShape.compactnessLabel}.` : ""),
      carryDetail:
        routeFollowUpMemory?.carryLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.currentLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.followUpLabel
          ? `${tr("Carry")}: ${routeFollowUpMemory.carryLabel}`
          : undefined,
      primaryActionKind: "resume",
      primaryLabel: tr("Resume route"),
      secondaryHref: routes.dashboard,
      secondaryLabel: tr("Open route home"),
      toneClassName: "border-accent/20 bg-accent/8",
    };
  }

  if (dailyLoopPlan && !dailyLoopPlan.lessonRunId && !dailyLoopPlan.completedAt) {
    const isRouteRescue = routeCadenceMemory?.status === "route_rescue";
    const isGentleReentry = routeCadenceMemory?.status === "gentle_reentry";
    const isSteadyReturn = routeCadenceMemory?.status === "steady_return";
    return {
      id: `waiting:${dailyLoopPlan.id}:${journeyState?.updatedAt ?? "stable"}`,
      title: routeEntryReleaseLabel
        ? dayShape?.substageLabel === tr("Ready to widen")
          ? tr("Your support route is stable enough to widen")
          : dayShape?.substageLabel === tr("Settling pass")
            ? tr("Your support route is settling back in")
            : tr("Your support route is ready to reopen")
        : isRouteRescue
          ? tr("Your route is ready for a gentle restart")
          : isGentleReentry
            ? tr("Your route is ready to reopen")
            : isSteadyReturn
              ? tr("Today's route is ready to keep the rhythm")
              : tr("Today's route is waiting for you"),
      description: routeCadenceMemory?.summary ?? journeyState?.nextBestAction ?? dailyLoopPlan.nextStepHint,
      detail:
        `${tr("Focus")}: ${dailyLoopPlan.focusArea}. ${tr("Session")}: ${dailyLoopPlan.recommendedLessonTitle}.` +
        (dayShape ? ` ${tr("Day shape")}: ${dayShape.title} · ${dayShape.compactnessLabel}.` : "") +
        (dayShape?.substageLabel ? ` ${tr("Reopen stage")}: ${dayShape.substageLabel}.` : "") +
        (dayShape?.expansionStageLabel ? ` ${tr("Expansion stage")}: ${dayShape.expansionStageLabel}.` : "") +
        (dayShape?.expansionWindowLabel ? ` ${dayShape.expansionWindowLabel}.` : "") +
        (dayShape?.sequenceLabel ? ` ${tr("Re-entry step")}: ${dayShape.sequenceLabel}.` : "") +
        (followUpHint ? ` ${followUpHint}` : "") +
        (routeEntryResetLabel ? ` ${tr("Reset target")}: ${routeEntryResetLabel}.` : "") +
        (routeEntryReleaseLabel ? ` ${tr("Ready to reopen")}: ${routeEntryReleaseLabel}.` : "") +
        (routeCadenceMemory?.actionHint ? ` ${routeCadenceMemory.actionHint}` : "") +
        (routeRecoveryMemory
          ? ` ${tr("Recovery arc")}: ${routeRecoveryMemory.summary}`
          : "") +
        (strategyMemory
          ? ` ${tr("Long memory")}: ${strategyMemory.focusSkill} ${strategyMemory.persistenceLevel}.`
          : skillTrajectory
            ? ` ${tr("Multi-day memory")}: ${skillTrajectory.focusSkill} ${skillTrajectory.direction}.`
            : ""),
      carryDetail:
        routeFollowUpMemory?.carryLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.currentLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.followUpLabel
          ? `${tr("Carry")}: ${routeFollowUpMemory.carryLabel}`
          : undefined,
      primaryActionKind: "start",
      primaryLabel: isRouteRescue ? tr("Restart gently") : tr("Start today’s route"),
      secondaryHref: routes.dailyLoop,
      secondaryLabel: tr("Open route preview"),
      toneClassName: isRouteRescue ? "border-accent/20 bg-accent/8" : "border-coral/20 bg-white/78",
    };
  }

  if (dailyLoopPlan?.completedAt && tomorrowPreview) {
    const practiceShift = sessionSummary?.practiceMixEvaluation?.summaryLine;
    return {
      id: `tomorrow:${dailyLoopPlan.id}:${journeyState?.updatedAt ?? "stable"}`,
      title: tr("Today's route is complete"),
      description: sessionSummary?.headline ?? tomorrowPreview.headline,
      detail:
        (dayShape
          ? `${tr("Day shape")}: ${dayShape.title} · ${dayShape.compactnessLabel}. `
          : "") +
        (
          practiceShift ??
          routeRecoveryMemory?.summary ??
          sessionSummary?.strategyShift ??
          routeCadenceMemory?.summary ??
          strategyMemory?.summary ??
          skillTrajectory?.summary ??
          tomorrowPreview.nextStepHint
        ),
      carryDetail:
        routeFollowUpMemory?.carryLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.currentLabel &&
        routeFollowUpMemory.carryLabel !== routeFollowUpMemory.followUpLabel
          ? `${tr("Carry")}: ${routeFollowUpMemory.carryLabel}`
          : undefined,
      primaryActionKind: "open_dashboard",
      primaryLabel: tr("Review tomorrow’s route"),
      secondaryHref: routes.activity,
      secondaryLabel: tr("Open the route trail"),
      toneClassName: "border-accent/20 bg-accent/8",
    };
  }

  return null;
}

export function JourneyReentryPrompt({
  dashboard,
  pathname,
  onOpenDashboard,
  onResumeRoute,
  onStartTodayRoute,
  tr,
}: JourneyReentryPromptProps) {
  const prompt = useMemo(
    () => (dashboard ? buildPromptModel(dashboard, tr) : null),
    [dashboard, tr],
  );
  const [dismissedKey, setDismissedKey] = useState<string | null>(() => readDismissedJourneyReentryKey());

  useEffect(() => {
    setDismissedKey(readDismissedJourneyReentryKey());
  }, [prompt?.id]);

  if (!dashboard || hiddenPaths.has(pathname) || !prompt || dismissedKey === prompt.id) {
    return null;
  }

  const activePrompt = prompt;

  async function handlePrimaryAction() {
    if (activePrompt.primaryActionKind === "start") {
      await onStartTodayRoute();
      return;
    }

    if (activePrompt.primaryActionKind === "open_dashboard") {
      onOpenDashboard();
      return;
    }

    await onResumeRoute();
  }

  function handleDismiss() {
    writeDismissedJourneyReentryKey(activePrompt.id);
    setDismissedKey(activePrompt.id);
  }

  return (
    <div className={`mt-4 rounded-[28px] border p-4 shadow-soft backdrop-blur ${activePrompt.toneClassName}`}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="text-[0.68rem] uppercase tracking-[0.22em] text-coral">{tr("Route reminder")}</div>
          <div className="mt-2 text-lg font-[700] tracking-[-0.02em] text-ink">{activePrompt.title}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{activePrompt.description}</div>
          <div className="mt-3 rounded-[20px] bg-white/78 px-4 py-3 text-sm text-slate-700">{activePrompt.detail}</div>
          {activePrompt.carryDetail ? (
            <div className="mt-3 rounded-[20px] bg-sand/70 px-4 py-3 text-sm text-slate-700">
              {activePrompt.carryDetail}
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 flex-wrap gap-3">
          <Button type="button" onClick={() => void handlePrimaryAction()}>
            {activePrompt.primaryLabel}
          </Button>
          <Link to={activePrompt.secondaryHref} className="proof-lesson-secondary-action">
            {activePrompt.secondaryLabel}
          </Link>
          <Button type="button" variant="ghost" onClick={handleDismiss}>
            {tr("Hide reminder")}
          </Button>
        </div>
      </div>
    </div>
  );
}

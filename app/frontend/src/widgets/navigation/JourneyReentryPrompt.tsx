import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
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

  if (resumeLesson) {
    return {
      id: `resume:${resumeLesson.runId}:${journeyState?.updatedAt ?? "stable"}`,
      title: tr("Your route is already in progress"),
      description: tr("You already have an active guided session. The strongest move right now is to return to it, not switch into a new module."),
      detail: `${tr("Current block")}: ${tr(resumeLesson.currentBlockTitle)}. ${tr("Progress")}: ${resumeLesson.completedBlocks}/${resumeLesson.totalBlocks}.`,
      primaryActionKind: "resume",
      primaryLabel: tr("Resume route"),
      secondaryHref: routes.dashboard,
      secondaryLabel: tr("Open dashboard"),
      toneClassName: "border-accent/20 bg-accent/8",
    };
  }

  if (dailyLoopPlan && !dailyLoopPlan.lessonRunId && !dailyLoopPlan.completedAt) {
    return {
      id: `waiting:${dailyLoopPlan.id}:${journeyState?.updatedAt ?? "stable"}`,
      title: tr("Today's route is waiting for you"),
      description: journeyState?.nextBestAction ?? dailyLoopPlan.nextStepHint,
      detail: `${tr("Focus")}: ${dailyLoopPlan.focusArea}. ${tr("Session")}: ${dailyLoopPlan.recommendedLessonTitle}.`,
      primaryActionKind: "start",
      primaryLabel: tr("Start today’s route"),
      secondaryHref: routes.dailyLoop,
      secondaryLabel: tr("Review the route"),
      toneClassName: "border-coral/20 bg-white/78",
    };
  }

  if (dailyLoopPlan?.completedAt && tomorrowPreview) {
    const practiceShift = sessionSummary?.practiceMixEvaluation?.summaryLine;
    return {
      id: `tomorrow:${dailyLoopPlan.id}:${journeyState?.updatedAt ?? "stable"}`,
      title: tr("Today's route is complete"),
      description: sessionSummary?.headline ?? tomorrowPreview.headline,
      detail: practiceShift ?? sessionSummary?.strategyShift ?? tomorrowPreview.nextStepHint,
      primaryActionKind: "open_dashboard",
      primaryLabel: tr("Review tomorrow’s route"),
      secondaryHref: routes.activity,
      secondaryLabel: tr("Open activity trail"),
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

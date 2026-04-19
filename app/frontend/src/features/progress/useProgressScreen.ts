import { useNavigate } from "react-router-dom";
import type { SpeakingAttempt } from "../../shared/types/app-data";
import { useActivityInsights } from "../../shared/activity/useActivityInsights";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { buildRoutePriorityView } from "../../shared/journey/route-priority";
import { useAppStore } from "../../shared/store/app-store";

export function useProgressScreen() {
  const { tr, tt, tl, formatDate, formatDateTime, formatDays, formatRoadmapSummary, locale } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const progress = useAppStore((state) => state.progress);
  const diagnosticRoadmap = useAppStore((state) => state.diagnosticRoadmap);
  const startLesson = useAppStore((state) => state.startLesson);
  const startTodayDailyLoop = useAppStore((state) => state.startTodayDailyLoop);
  const startDiagnosticCheckpoint = useAppStore((state) => state.startDiagnosticCheckpoint);
  const navigate = useNavigate();
  const { activityError, listeningAttempts, listeningTrend, pronunciationTrend, speakingAttempts } =
    useActivityInsights({
      errorMessage: "Failed to load speaking or pronunciation activity",
      includeListeningHistory: true,
    });

  const dailyGoalProgress = progress
    ? Math.min(
        100,
        Math.round((progress.minutesCompletedToday / Math.max(progress.dailyGoalMinutes, 1)) * 100),
      )
    : 0;
  const averageLessonScore =
    progress && progress.history.length > 0
      ? Math.round(progress.history.reduce((total, item) => total + item.score, 0) / progress.history.length)
      : 0;
  const mostRecentLesson = progress?.history[0] ?? null;
  const recentSpeakingAttempts = speakingAttempts.slice(0, 4);
  const roadmapSummary = diagnosticRoadmap
    ? formatRoadmapSummary({
        declaredCurrentLevel: diagnosticRoadmap.declaredCurrentLevel,
        estimatedLevel: diagnosticRoadmap.estimatedLevel,
        targetLevel: diagnosticRoadmap.targetLevel,
        weakestSkills: diagnosticRoadmap.weakestSkills,
        nextFocus: diagnosticRoadmap.nextFocus,
      })
    : null;

  const feedbackSourceLabel = (source: SpeakingAttempt["feedbackSource"]) =>
    source === "mock" ? tr("fallback") : tr(source);

  async function handleStartCheckpoint() {
    await startDiagnosticCheckpoint();
    navigate(routes.lessonRunner);
  }

  const hasAvailableDailyRoute =
    Boolean(dashboard?.dailyLoopPlan) && dashboard?.dailyLoopPlan?.completedAt == null;
  const hasActiveDailyRoute =
    Boolean(dashboard?.dailyLoopPlan?.lessonRunId) && dashboard?.dailyLoopPlan?.completedAt == null;
  const routePriorityView = buildRoutePriorityView(dashboard ?? null, tr);
  const primaryRouteLabel = routePriorityView.label;

  async function handleStartPrimaryRoute() {
    if (routePriorityView.primaryRoute !== routes.dailyLoop && routePriorityView.primaryRoute !== routes.lessonRunner) {
      navigate(routePriorityView.primaryRoute);
      return;
    }

    if (hasAvailableDailyRoute) {
      await startTodayDailyLoop();
    } else if (routePriorityView.mode === "checkpoint") {
      await startDiagnosticCheckpoint();
    } else {
      await startLesson();
    }
    navigate(routes.lessonRunner);
  }

  return {
    activityError,
    averageLessonScore,
    dashboard,
    dailyGoalProgress,
    diagnosticRoadmap,
    feedbackSourceLabel,
    formatDate,
    formatDateTime,
    formatDays,
    handleStartPrimaryRoute,
    handleStartCheckpoint,
    hasActiveDailyRoute,
    hasAvailableDailyRoute,
    listeningAttempts,
    listeningTrend,
    mostRecentLesson,
    primaryRouteLabel,
    progress,
    pronunciationTrend,
    recentSpeakingAttempts,
    routePriorityView,
    roadmapSummary,
    studyLoop: dashboard?.studyLoop ?? null,
    locale,
    tl,
    tr,
    tt,
  };
}

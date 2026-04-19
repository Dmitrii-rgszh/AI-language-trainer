import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { useActivityInsights } from "../../shared/activity/useActivityInsights";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { buildRoutePriorityView } from "../../shared/journey/route-priority";
import { useAppStore } from "../../shared/store/app-store";

export type ActivityEvent = {
  id: string;
  title: string;
  kind: "lesson" | "speaking" | "result";
  meta: string;
  detail: string;
  createdAt: string;
  route: string;
};

export function useActivityScreen() {
  const { tr, tt, formatDateTime, formatDays, locale } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const bootstrap = useAppStore((state) => state.bootstrap);
  const startLesson = useAppStore((state) => state.startLesson);
  const startTodayDailyLoop = useAppStore((state) => state.startTodayDailyLoop);
  const startDiagnosticCheckpoint = useAppStore((state) => state.startDiagnosticCheckpoint);
  const startRecoveryLesson = useAppStore((state) => state.startRecoveryLesson);
  const progress = useAppStore((state) => state.progress);
  const mistakes = useAppStore((state) => state.mistakes);
  const lastLessonResult = useAppStore((state) => state.lastLessonResult);
  const navigate = useNavigate();
  const [reviewingVocabularyId, setReviewingVocabularyId] = useState<string | null>(null);
  const { activityError, listeningTrend, pronunciationTrend, speakingAttempts } = useActivityInsights({
    errorMessage: "Failed to load speaking or pronunciation activity",
  });

  const recentEvents = useMemo<ActivityEvent[]>(() => {
    const lessonEvents =
      progress?.history.map((item) => ({
        id: `lesson-${item.id}`,
        title: item.title,
        kind: "lesson" as const,
        meta: `${item.lessonType} lesson`,
        detail: `Completed with score ${item.score}.`,
        createdAt: item.completedAt,
        route: routes.progress,
      })) ?? [];

    const speakingEvents = speakingAttempts.map((attempt) => ({
      id: `speaking-${attempt.id}`,
      title: attempt.scenarioTitle,
      kind: "speaking" as const,
      meta: `${attempt.inputMode} speaking`,
      detail: attempt.feedbackSummary,
      createdAt: attempt.createdAt,
      route: routes.speaking,
    }));

    const pronunciationEvents =
      pronunciationTrend && pronunciationTrend.recentAttempts > 0
        ? [
            {
              id: "pronunciation-trend",
              title: "Pronunciation trend updated",
              kind: "result" as const,
              meta: "audio pronunciation",
              detail:
                pronunciationTrend.weakestSounds.length > 0
                  ? `Top weak sounds: ${pronunciationTrend.weakestSounds
                      .slice(0, 2)
                      .map((item) => item.label)
                      .join(", ")}.`
                  : "Recent pronunciation checks look stable.",
              createdAt: new Date().toISOString(),
              route: routes.pronunciation,
            },
          ]
        : [];

    const listeningEvents =
      listeningTrend && listeningTrend.recentAttempts > 0
        ? [
            {
              id: "listening-trend",
              title: "Listening trend updated",
              kind: "result" as const,
              meta: "audio listening",
              detail:
                listeningTrend.weakestPrompts.length > 0
                  ? `Weak prompt cluster: ${listeningTrend.weakestPrompts[0].label}.`
                  : "Listening answers are currently more stable.",
              createdAt: new Date().toISOString(),
              route: routes.progress,
            },
          ]
        : [];

    const resultEvents = lastLessonResult
      ? [
          {
            id: `result-${lastLessonResult.runId}`,
            title: lastLessonResult.title,
            kind: "result" as const,
            meta: "current session result",
            detail: `Score ${lastLessonResult.score}. Mistakes found: ${lastLessonResult.mistakes.length}.`,
            createdAt: lastLessonResult.completedAt ?? "",
            route: routes.lessonResults,
          },
        ]
      : [];

    return [...lessonEvents, ...speakingEvents, ...pronunciationEvents, ...listeningEvents, ...resultEvents]
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .slice(0, 12);
  }, [lastLessonResult, listeningTrend, progress?.history, pronunciationTrend, speakingAttempts]);

  const topMistakes = useMemo(
    () => [...mistakes].sort((left, right) => right.repetitionCount - left.repetitionCount).slice(0, 6),
    [mistakes],
  );

  async function handleVocabularyReview(itemId: string) {
    setReviewingVocabularyId(itemId);
    try {
      await apiClient.reviewVocabularyItem(itemId, true);
      await bootstrap();
    } finally {
      setReviewingVocabularyId(null);
    }
  }

  async function handleStartRecoveryLesson() {
    await startRecoveryLesson();
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
    } else if (routePriorityView.mode === "recovery") {
      await startRecoveryLesson();
    } else {
      await startLesson();
    }
    navigate(routes.lessonRunner);
  }

  return {
    activityError,
    dashboard,
    formatDateTime,
    formatDays,
    handleStartPrimaryRoute,
    handleStartRecoveryLesson,
    handleVocabularyReview,
    hasAvailableDailyRoute,
    hasActiveDailyRoute,
    lastLessonResult,
    locale,
    listeningTrend,
    mistakes,
    primaryRouteLabel,
    progress,
    pronunciationTrend,
    recentEvents,
    reviewingVocabularyId,
    routePriorityView,
    speakingAttempts,
    studyLoop: dashboard?.studyLoop ?? null,
    topMistakes,
    tr,
    tt,
  };
}

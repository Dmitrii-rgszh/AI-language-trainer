import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import type { PronunciationTrend, ProviderStatus, QuickAction, SpeakingAttempt } from "../../shared/types/app-data";

export type DashboardActivityEvent = {
  id: string;
  title: string;
  meta: string;
  detail: string;
  createdAt: string;
  route: string;
};

export function useDashboardScreen() {
  const {
    locale,
    tr,
    tt,
    tl,
    formatDateTime,
    formatAdaptiveHeadline,
    formatAdaptiveSummary,
    formatRecommendationGoal,
    formatRoadmapSummary,
  } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const diagnosticRoadmap = useAppStore((state) => state.diagnosticRoadmap);
  const bootstrap = useAppStore((state) => state.bootstrap);
  const providers = useAppStore((state) => state.providers);
  const startLesson = useAppStore((state) => state.startLesson);
  const startDiagnosticCheckpoint = useAppStore((state) => state.startDiagnosticCheckpoint);
  const startRecoveryLesson = useAppStore((state) => state.startRecoveryLesson);
  const discardLessonRun = useAppStore((state) => state.discardLessonRun);
  const restartLesson = useAppStore((state) => state.restartLesson);
  const navigate = useNavigate();
  const [speakingAttempts, setSpeakingAttempts] = useState<SpeakingAttempt[]>([]);
  const [pronunciationTrend, setPronunciationTrend] = useState<PronunciationTrend | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [reviewingVocabularyId, setReviewingVocabularyId] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadRecentActivity() {
      try {
        const [attempts, trend] = await Promise.all([
          apiClient.getSpeakingAttempts(),
          apiClient.getPronunciationTrends(),
        ]);
        if (isMounted) {
          setSpeakingAttempts(attempts);
          setPronunciationTrend(trend);
          setActivityError(null);
        }
      } catch (error) {
        if (isMounted) {
          setActivityError(error instanceof Error ? error.message : "Failed to load recent speaking activity");
        }
      }
    }

    void loadRecentActivity();

    return () => {
      isMounted = false;
    };
  }, []);

  const recentActivity = useMemo<DashboardActivityEvent[]>(() => {
    const lessonEvents = (dashboard?.progress.history ?? []).slice(0, 4).map((item) => ({
      id: `lesson-${item.id}`,
      title: item.title,
      meta: `${item.lessonType} lesson`,
      detail: `Completed with score ${item.score}`,
      createdAt: item.completedAt,
      route: routes.progress,
    }));
    const speakingEvents = speakingAttempts.slice(0, 4).map((attempt) => ({
      id: `speaking-${attempt.id}`,
      title: attempt.scenarioTitle,
      meta: `${attempt.inputMode} speaking`,
      detail: attempt.feedbackSummary,
      createdAt: attempt.createdAt,
      route: routes.speaking,
    }));
    const pronunciationEvents =
      pronunciationTrend && pronunciationTrend.recentAttempts > 0
        ? [
            {
              id: "pronunciation-dashboard-trend",
              title: "Pronunciation trend",
              meta: "audio pronunciation",
              detail:
                pronunciationTrend.weakestSounds.length > 0
                  ? `Weak sound in rotation: ${pronunciationTrend.weakestSounds[0].label}.`
                  : "Pronunciation checks currently look stable.",
              createdAt: new Date().toISOString(),
              route: routes.pronunciation,
            },
          ]
        : [];

    return [...lessonEvents, ...speakingEvents, ...pronunciationEvents]
      .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
      .slice(0, 6);
  }, [dashboard?.progress.history, pronunciationTrend, speakingAttempts]);

  const dailyGoalProgress = dashboard
    ? Math.min(
        100,
        Math.round(
          (dashboard.progress.minutesCompletedToday / Math.max(dashboard.progress.dailyGoalMinutes, 1)) * 100,
        ),
      )
    : 0;
  const readyProviders = providers.filter((provider) => provider.status === "ready").length;
  const totalProviders = providers.length;
  const fallbackProviders = providers.filter((provider) => provider.status === "mock").length;
  const disabledProviders = providers.filter((provider) => provider.status === "offline").length;
  const recoveringSignals =
    dashboard?.studyLoop?.mistakeResolution?.filter(
      (item) => item.status === "recovering" || item.status === "stabilizing",
    ) ?? [];
  const recommendationGoal = dashboard
    ? formatRecommendationGoal({
        lessonType: dashboard.recommendation.lessonType,
        focusArea: dashboard.recommendation.focusArea,
        weakSpotTitles: dashboard.weakSpots.map((spot) => spot.title),
        dueVocabularyCount: dashboard.studyLoop?.vocabularySummary.dueCount ?? 0,
        professionTrack: dashboard.profile.professionTrack,
      })
    : null;
  const adaptiveHeadline =
    dashboard?.studyLoop ? formatAdaptiveHeadline(dashboard.profile.name, dashboard.studyLoop.focusArea) : null;
  const adaptiveSummary = dashboard?.studyLoop
    ? formatAdaptiveSummary({
        weakSpotTitle: dashboard.studyLoop.weakSpots[0]?.title,
        dueVocabularyCount: dashboard.studyLoop.vocabularySummary.dueCount,
        listeningFocus: dashboard.studyLoop.listeningFocus,
        activeVocabularyCount: dashboard.studyLoop.vocabularySummary.activeCount,
        masteredVocabularyCount: dashboard.studyLoop.vocabularySummary.masteredCount,
        minutesCompletedToday: dashboard.progress.minutesCompletedToday,
      })
    : null;
  const roadmapSummary = diagnosticRoadmap
    ? formatRoadmapSummary({
        declaredCurrentLevel: diagnosticRoadmap.declaredCurrentLevel,
        estimatedLevel: diagnosticRoadmap.estimatedLevel,
        targetLevel: diagnosticRoadmap.targetLevel,
        weakestSkills: diagnosticRoadmap.weakestSkills,
        nextFocus: diagnosticRoadmap.nextFocus,
      })
    : null;

  const extendedQuickActions: QuickAction[] = dashboard
    ? [
        ...dashboard.quickActions,
        {
          id: "activity-center",
          title: tr("Open activity center"),
          description: tr("See lesson history, speaking attempts, current results and mistake patterns in one place."),
          route: routes.activity,
        },
        {
          id: "edit-profile",
          title: tr("Update profile"),
          description: tr("Adjust current level, target, lesson duration and priority mix without leaving the base flow."),
          route: routes.settings,
        },
      ]
    : [];

  async function handleStartLesson() {
    await startLesson();
    navigate(routes.lessonRunner);
  }

  async function handleStartRecoveryLesson() {
    await startRecoveryLesson();
    navigate(routes.lessonRunner);
  }

  async function handleStartDiagnosticCheckpoint() {
    await startDiagnosticCheckpoint();
    navigate(routes.lessonRunner);
  }

  async function handleVocabularyReview(itemId: string) {
    setReviewingVocabularyId(itemId);
    try {
      await apiClient.reviewVocabularyItem(itemId, true);
      await bootstrap();
    } finally {
      setReviewingVocabularyId(null);
    }
  }

  async function handleRestartLesson() {
    await restartLesson();
  }

  async function handleDiscardLessonRun() {
    await discardLessonRun();
  }

  function openLessonRunner() {
    navigate(routes.lessonRunner);
  }

  return {
    activityError,
    adaptiveHeadline,
    adaptiveSummary,
    dailyGoalProgress,
    dashboard,
    diagnosticRoadmap,
    disabledProviders,
    extendedQuickActions,
    fallbackProviders,
    formatDateTime,
    handleDiscardLessonRun,
    handleRestartLesson,
    handleStartDiagnosticCheckpoint,
    handleStartLesson,
    handleStartRecoveryLesson,
    handleVocabularyReview,
    locale,
    openLessonRunner,
    pronunciationTrend,
    providers,
    readyProviders,
    recentActivity,
    recommendationGoal,
    recoveringSignals,
    reviewingVocabularyId,
    roadmapSummary,
    tl,
    totalProviders,
    tr,
    tt,
  };
}

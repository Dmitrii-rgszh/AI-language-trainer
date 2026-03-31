import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import type { PronunciationTrend, SpeakingAttempt } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function DashboardScreen() {
  const { tr, tt, tl, formatDateTime } = useLocale();
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

  const recentActivity = useMemo(() => {
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

  if (!dashboard) {
    return <Card>{tr("Подгружаю dashboard...")}</Card>;
  }

  const dailyGoalProgress = Math.min(
    100,
    Math.round((dashboard.progress.minutesCompletedToday / Math.max(dashboard.progress.dailyGoalMinutes, 1)) * 100),
  );
  const readyProviders = providers.filter((provider) => provider.status === "ready").length;
  const totalProviders = providers.length;
  const fallbackProviders = providers.filter((provider) => provider.status === "mock").length;
  const disabledProviders = providers.filter((provider) => provider.status === "offline").length;
  const recoveringSignals =
    dashboard.studyLoop?.mistakeResolution?.filter((item) => item.status === "recovering" || item.status === "stabilizing") ?? [];

  const handleStartLesson = async () => {
    await startLesson();
    navigate(routes.lessonRunner);
  };
  const handleStartRecoveryLesson = async () => {
    await startRecoveryLesson();
    navigate(routes.lessonRunner);
  };
  const handleStartDiagnosticCheckpoint = async () => {
    await startDiagnosticCheckpoint();
    navigate(routes.lessonRunner);
  };
  const handleVocabularyReview = async (itemId: string) => {
    setReviewingVocabularyId(itemId);
    try {
      await apiClient.reviewVocabularyItem(itemId, true);
      await bootstrap();
    } finally {
      setReviewingVocabularyId(null);
    }
  };

  const extendedQuickActions = [
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
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Dashboard")}
        title={`${tr("Welcome back")}, ${dashboard.profile.name}`}
        description={tr(
          "Главный экран уже собирает recommended lesson, слабые места, quick actions и skill progress из общего состояния приложения.",
        )}
      />

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Recommended lesson")}</div>
          <div className="text-2xl font-semibold text-ink">{tr(dashboard.recommendation.title)}</div>
          <div className="text-sm leading-6 text-slate-600">{tr(dashboard.recommendation.goal)}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Duration")}: {dashboard.recommendation.duration} min. {tr("Focus")}:{" "}
            {tl(dashboard.recommendation.focusArea.split(","))}.
          </div>
          {recoveringSignals.length > 0 ? (
            <div className="rounded-2xl bg-mint/30 p-4 text-sm text-slate-700">
              {tr("Recovery pressure is easing for")}{" "}
              {recoveringSignals.map((item) => tr(item.weakSpotTitle)).join(", ")}.{" "}
              {tr("The roadmap can lean back toward the main lesson flow.")}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => void handleStartLesson()}>{tr("Start lesson")}</Button>
            <Link
              to={routes.progress}
              className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
            >
              {tr("See progress")}
            </Link>
          </div>
        </Card>

        <Card className="grid gap-3 sm:grid-cols-2">
          <ScoreBadge label={tr("Grammar")} score={dashboard.progress.grammarScore} />
          <ScoreBadge label={tr("Speaking")} score={dashboard.progress.speakingScore} />
          <ScoreBadge label={tr("Writing")} score={dashboard.progress.writingScore} />
          <ScoreBadge label={tr("Profession")} score={dashboard.progress.professionScore} />
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Today")}</div>
          <div className="text-3xl font-semibold text-ink">
            {dashboard.progress.minutesCompletedToday}/{dashboard.progress.dailyGoalMinutes} min
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-sand">
            <div className="h-full rounded-full bg-accent" style={{ width: `${dailyGoalProgress}%` }} />
          </div>
          <div className="text-sm text-slate-600">{tr("Daily goal completion")}: {dailyGoalProgress}%</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Consistency")}</div>
          <div className="text-3xl font-semibold text-ink">{dashboard.progress.streak} days</div>
          <div className="text-sm text-slate-600">{tr("Current streak and habit continuity across your recent sessions.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Runtime Stack")}</div>
          <div className="text-3xl font-semibold text-ink">
            {readyProviders}/{totalProviders}
          </div>
          <div className="text-sm text-slate-600">
            {tr("Ready")}: {readyProviders}, {tr("fallback")}: {fallbackProviders}, {tr("offline")}: {disabledProviders}.
          </div>
        </Card>
      </div>

      {diagnosticRoadmap ? (
        <Card className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Level roadmap")}</div>
              <div className="mt-2 text-2xl font-semibold text-ink">
                {diagnosticRoadmap.estimatedLevel} {"->"} {diagnosticRoadmap.targetLevel}
              </div>
            </div>
            <Link
              to={routes.progress}
              className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
            >
              {tr("Open roadmap")}
            </Link>
          </div>
          <div className="text-sm leading-6 text-slate-600">{tr(diagnosticRoadmap.summary)}</div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Declared level")}: <span className="font-semibold text-ink">{diagnosticRoadmap.declaredCurrentLevel}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Estimated level")}: <span className="font-semibold text-ink">{diagnosticRoadmap.estimatedLevel}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Overall score")}: <span className="font-semibold text-ink">{diagnosticRoadmap.overallScore}</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="secondary" onClick={() => void handleStartDiagnosticCheckpoint()}>
              {tr("Run checkpoint")}
            </Button>
            <Button onClick={() => void handleStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
          </div>
        </Card>
      ) : null}

      {dashboard.resumeLesson ? (
        <Card className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Resume lesson")}</div>
          <div className="text-2xl font-semibold text-ink">{tr(dashboard.resumeLesson.title)}</div>
          <div className="text-sm text-slate-600">
            {tr("Current block")}: {tr(dashboard.resumeLesson.currentBlockTitle)}
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Progress")}: {dashboard.resumeLesson.completedBlocks}/{dashboard.resumeLesson.totalBlocks} {tr("blocks completed")}.
          </div>
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => navigate(routes.lessonRunner)}>{tr("Resume lesson")}</Button>
            <Button variant="secondary" onClick={() => void restartLesson()}>
              {tr("Restart lesson")}
            </Button>
            <Button variant="ghost" onClick={() => void discardLessonRun()}>
              {tr("Discard draft")}
            </Button>
          </div>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Weak spots")}</div>
            <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
              {dashboard.weakSpots.length} {tr("active")}
            </div>
          </div>
          {dashboard.weakSpots.map((spot) => (
            <div key={spot.id} className="rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr(spot.title)}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(spot.category)}</div>
              <div className="mt-2 text-sm text-slate-600">{tr(spot.recommendation)}</div>
            </div>
          ))}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Quick actions")}</div>
          {extendedQuickActions.map((action) => (
            <Link key={action.id} to={action.route} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr(action.title)}</div>
              <div className="mt-2 text-sm text-slate-600">{tr(action.description)}</div>
            </Link>
          ))}
        </Card>
      </div>

      {dashboard.studyLoop ? (
        <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="space-y-4">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Adaptive study loop")}</div>
            <div className="text-2xl font-semibold text-ink">{tr(dashboard.studyLoop.headline)}</div>
            <div className="text-sm leading-6 text-slate-600">{tr(dashboard.studyLoop.summary)}</div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Due vocab")}: <span className="font-semibold text-ink">{dashboard.studyLoop.vocabularySummary.dueCount}</span>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Active vocab")}: <span className="font-semibold text-ink">{dashboard.studyLoop.vocabularySummary.activeCount}</span>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Listening focus")}:{" "}
                <span className="font-semibold text-ink">
                  {dashboard.studyLoop.listeningFocus ? tt(dashboard.studyLoop.listeningFocus) : tr("stable")}
                </span>
              </div>
            </div>
            <div className="rounded-2xl bg-sand/80 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Why this loop was generated")}</div>
              <div className="mt-3 space-y-2 text-sm text-slate-600">
                {dashboard.studyLoop.generationRationale.map((item) => (
                  <div key={item}>• {tr(item)}</div>
                ))}
              </div>
            </div>
            {dashboard.studyLoop.moduleRotation.length > 0 ? (
              <div className="rounded-2xl bg-white/70 p-4">
                <div className="text-sm font-semibold text-ink">{tr("Main flow rotation")}</div>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  {dashboard.studyLoop.moduleRotation.slice(0, 3).map((item) => (
                    <Link key={item.moduleKey} to={item.route} className="rounded-2xl bg-sand/80 p-4">
                      <div className="text-xs uppercase tracking-[0.16em] text-coral">
                        {tr("priority")} {item.priority}
                      </div>
                      <div className="mt-2 text-sm font-semibold text-ink">{tr(item.title)}</div>
                      <div className="mt-2 text-sm text-slate-600">{tr(item.reason)}</div>
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => void handleStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
              <Link
                to={routes.activity}
                className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
              >
                {tr("Open full loop")}
              </Link>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {dashboard.studyLoop.nextSteps.map((step) => (
                <Link key={step.id} to={step.route} className="rounded-2xl bg-white/70 p-4">
                  <div className="text-sm font-semibold text-ink">{tr(step.title)}</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.16em] text-coral">{tt(step.stepType)}</div>
                  <div className="mt-3 text-sm text-slate-600">{tr(step.description)}</div>
                </Link>
              ))}
            </div>
          </Card>

          <Card className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-lg font-semibold text-ink">{tr("Vocabulary due now")}</div>
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                {dashboard.studyLoop.dueVocabulary.length} {tr("cards")}
              </div>
            </div>
            <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {tr("Queue balance")}: {dashboard.studyLoop.vocabularySummary.newCount} {tr("new")},{" "}
              {dashboard.studyLoop.vocabularySummary.activeCount} {tr("active")},{" "}
              {dashboard.studyLoop.vocabularySummary.masteredCount} {tr("mastered")}.
              {dashboard.studyLoop.vocabularySummary.weakestCategory
                ? ` ${tr("Most loaded category")}: ${tt(dashboard.studyLoop.vocabularySummary.weakestCategory)}.`
                : ""}
            </div>
            {dashboard.studyLoop.dueVocabulary.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                {tr("No urgent vocabulary reviews right now. Stay with the current lesson flow.")}
              </div>
            ) : (
              dashboard.studyLoop.dueVocabulary.map((item) => (
                <div key={item.id} className="rounded-2xl bg-white/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-ink">{item.word}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{item.translation}</div>
                    </div>
                    <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                      {tr("stage")} {item.repetitionStage}
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-slate-600">{item.context}</div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button
                      variant="secondary"
                      onClick={() => void handleVocabularyReview(item.id)}
                      disabled={reviewingVocabularyId === item.id}
                    >
                      {reviewingVocabularyId === item.id ? tr("Saving...") : tr("Mark reviewed")}
                    </Button>
                    <Link
                      to={routes.activity}
                      className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
                    >
                      {tr("Open activity")}
                    </Link>
                  </div>
                </div>
              ))
            )}
          </Card>
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Listening contribution")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Listening score")}: <span className="font-semibold text-ink">{dashboard.progress.listeningScore}</span>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {dashboard.studyLoop?.listeningFocus
              ? `Adaptive generation is currently compensating for ${dashboard.studyLoop.listeningFocus.replace(/_/g, " ")}.`
              : "Listening currently does not dominate the adaptive loop."}
          </div>
        </Card>
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Vocabulary contribution")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Due now")}: <span className="font-semibold text-ink">{dashboard.studyLoop?.vocabularySummary.dueCount ?? 0}</span>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {dashboard.studyLoop?.vocabularySummary.weakestCategory
              ? `Adaptive loop keeps surfacing vocabulary from ${dashboard.studyLoop.vocabularySummary.weakestCategory}.`
              : "Vocabulary queue is balanced enough that no single category dominates."}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Recent activity")}</div>
            <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open progress")}
            </Link>
          </div>
          {activityError ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {activityError}
            </div>
          ) : null}
          {recentActivity.length === 0 ? (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Activity will appear here after the first completed lesson or speaking attempt.")}
            </div>
          ) : (
            recentActivity.map((event) => (
              <Link key={event.id} to={event.route} className="block rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{tr(event.title)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(event.meta)}</div>
                  </div>
                  <div className="text-xs text-slate-500">{formatDateTime(event.createdAt)}</div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{tr(event.detail)}</div>
              </Link>
            ))
          )}
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Provider health")}</div>
            <Link to={routes.settings} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open settings")}
            </Link>
          </div>
          {providers.map((provider) => (
            <div key={provider.key} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{provider.name}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(provider.type)}</div>
                </div>
                <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">{tr(provider.status)}</div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{tr(provider.details)}</div>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import type { ListeningTrend, PronunciationTrend, SpeakingAttempt } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

type ActivityEvent = {
  id: string;
  title: string;
  kind: "lesson" | "speaking" | "result";
  meta: string;
  detail: string;
  createdAt: string;
  route: string;
};

function resolutionTone(status: string) {
  if (status === "stabilizing") {
    return "bg-mint/40 text-ink";
  }
  if (status === "recovering") {
    return "bg-sand text-ink";
  }
  return "bg-rose-100 text-rose-700";
}

export function ActivityScreen() {
  const { tr, tt, formatDateTime, formatDays } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const bootstrap = useAppStore((state) => state.bootstrap);
  const startRecoveryLesson = useAppStore((state) => state.startRecoveryLesson);
  const progress = useAppStore((state) => state.progress);
  const mistakes = useAppStore((state) => state.mistakes);
  const lastLessonResult = useAppStore((state) => state.lastLessonResult);
  const navigate = useNavigate();
  const [speakingAttempts, setSpeakingAttempts] = useState<SpeakingAttempt[]>([]);
  const [pronunciationTrend, setPronunciationTrend] = useState<PronunciationTrend | null>(null);
  const [listeningTrend, setListeningTrend] = useState<ListeningTrend | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [reviewingVocabularyId, setReviewingVocabularyId] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadActivitySupport() {
      try {
        const [attempts, trend, nextListeningTrend] = await Promise.all([
          apiClient.getSpeakingAttempts(),
          apiClient.getPronunciationTrends(),
          apiClient.getListeningTrends(),
        ]);
        if (isMounted) {
          setSpeakingAttempts(attempts);
          setPronunciationTrend(trend);
          setListeningTrend(nextListeningTrend);
          setActivityError(null);
        }
      } catch (error) {
        if (isMounted) {
          setActivityError(error instanceof Error ? error.message : "Failed to load speaking or pronunciation activity");
        }
      }
    }

    void loadActivitySupport();

    return () => {
      isMounted = false;
    };
  }, []);

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

  const topMistakes = [...mistakes].sort((left, right) => right.repetitionCount - left.repetitionCount).slice(0, 6);
  const handleVocabularyReview = async (itemId: string) => {
    setReviewingVocabularyId(itemId);
    try {
      await apiClient.reviewVocabularyItem(itemId, true);
      await bootstrap();
    } finally {
      setReviewingVocabularyId(null);
    }
  };
  const handleStartRecoveryLesson = async () => {
    await startRecoveryLesson();
    navigate(routes.lessonRunner);
  };

  if (!progress) {
    return <Card>{tr("Подгружаю activity...")}</Card>;
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Activity")}
        title={tr("Unified Activity And History")}
        description={tr("Единая точка истории по урокам, speaking practice, текущим lesson results и накопленным mistake patterns.")}
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Lessons")}</div>
          <div className="text-3xl font-semibold text-ink">{progress.history.length}</div>
          <div className="text-sm text-slate-600">{tr("Completed lessons in current progress history.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Speaking attempts")}</div>
          <div className="text-3xl font-semibold text-ink">{speakingAttempts.length}</div>
          <div className="text-sm text-slate-600">{tr("Voice and text practice attempts collected so far.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Open patterns")}</div>
          <div className="text-3xl font-semibold text-ink">{mistakes.length}</div>
          <div className="text-sm text-slate-600">{tr("Mistake records currently tracked in the system.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Latest result")}</div>
          <div className="text-3xl font-semibold text-ink">{lastLessonResult?.score ?? "-"}</div>
          <div className="text-sm text-slate-600">
            {lastLessonResult ? tr("Current session lesson result is available.") : tr("No current session result yet.")}
          </div>
        </Card>
      </div>

      {pronunciationTrend ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Pronunciation contribution")}</div>
            <Link to={routes.pronunciation} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open lab")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Average score")}: <span className="font-semibold text-ink">{pronunciationTrend.averageScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent checks")}: <span className="font-semibold text-ink">{pronunciationTrend.recentAttempts}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              Top weak sound: <span className="font-semibold text-ink">{pronunciationTrend.weakestSounds[0]?.label ?? tr("stable")}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {pronunciationTrend.weakestSounds.length > 0
              ? `This area is now part of the overall learning signal: ${pronunciationTrend.weakestSounds
                  .map((item) => `${item.label} (${item.occurrences}x)`)
                  .join(", ")}.`
              : "Pronunciation looks stable enough that no repeating weak sound is dominating activity yet."}
          </div>
        </Card>
      ) : null}

      {dashboard?.studyLoop ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Adaptive loop summary")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr(dashboard.studyLoop.summary)}</div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {tr("Due vocab")}: {dashboard.studyLoop.vocabularySummary.dueCount}
              </div>
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                Listening: {dashboard.studyLoop.listeningFocus ? tt(dashboard.studyLoop.listeningFocus) : tr("stable")}
              </div>
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                Weak vocab cat: {dashboard.studyLoop.vocabularySummary.weakestCategory ? tt(dashboard.studyLoop.vocabularySummary.weakestCategory) : "balanced"}
              </div>
            </div>
            <div className="rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Generation rationale")}</div>
              <div className="mt-3 space-y-2 text-sm text-slate-600">
                {dashboard.studyLoop.generationRationale.map((item) => (
                  <div key={item}>• {tr(item)}</div>
                ))}
              </div>
            </div>
            <Button onClick={() => void handleStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
            {dashboard.studyLoop.nextSteps.map((step) => (
              <Link key={step.id} to={step.route} className="block rounded-2xl bg-sand/80 p-4">
                <div className="text-sm font-semibold text-ink">{tr(step.title)}</div>
                <div className="mt-2 text-sm text-slate-600">{tr(step.description)}</div>
              </Link>
            ))}
          </Card>

          <Card className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-lg font-semibold text-ink">{tr("Vocabulary repetition")}</div>
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                {dashboard.studyLoop.dueVocabulary.length} {tr("due")}
              </div>
            </div>
            {dashboard.studyLoop.dueVocabulary.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Vocabulary queue is clear for now.")}</div>
            ) : (
              dashboard.studyLoop.dueVocabulary.map((item) => (
                <div key={item.id} className="rounded-2xl bg-white/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-ink">{item.word}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{item.translation}</div>
                    </div>
                    <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">{tt(item.learnedStatus)}</div>
                  </div>
                  <div className="mt-3 text-sm text-slate-600">{item.context}</div>
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={() => void handleVocabularyReview(item.id)}
                      disabled={reviewingVocabularyId === item.id}
                      className="rounded-full bg-ink px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-ink/85 disabled:opacity-60"
                    >
                      {reviewingVocabularyId === item.id ? tr("Saving...") : tr("Mark reviewed")}
                    </button>
                  </div>
                </div>
              ))
            )}
          </Card>
        </div>
        ) : null}

      {dashboard?.studyLoop?.vocabularyBacklinks?.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Mistake to vocabulary loop")}</div>
            <Link to={routes.vocabulary} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open hub")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {dashboard.studyLoop.vocabularyBacklinks.map((link) => (
              <div key={link.weakSpotTitle} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-ink">{tr(link.weakSpotTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(link.weakSpotCategory)}</div>
                  </div>
                  <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                    {link.dueCount} {tr("due")} / {link.activeCount} {tr("active")}
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{tr("Converted examples")}: {link.exampleWords.join(", ")}.</div>
                <div className="mt-2 text-xs uppercase tracking-[0.12em] text-slate-500">
                  {tr("sources")}: {link.sourceModules.map((item) => tt(item)).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {dashboard?.studyLoop?.mistakeResolution?.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Weak spot recovery visibility")}</div>
            <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open progress")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {dashboard.studyLoop.mistakeResolution.map((item) => (
              <div key={item.weakSpotTitle} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-ink">{tr(item.weakSpotTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.weakSpotCategory)}</div>
                  </div>
                  <div className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${resolutionTone(item.status)}`}>
                    {tr(item.status)}
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-600">
                  {tr("Repeats")}: {item.repetitionCount}. {tr("Last seen")} {formatDays(item.lastSeenDaysAgo)} ago. {tr("Linked vocabulary")}: {item.linkedVocabularyCount}.
                </div>
                <div className="mt-3 rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">{tr(item.resolutionHint)}</div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {dashboard?.studyLoop?.moduleRotation?.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Module rotation balance")}</div>
            <Link to={routes.dashboard} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open dashboard")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {dashboard.studyLoop.moduleRotation.slice(0, 3).map((item) => (
              <Link key={item.moduleKey} to={item.route} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.16em] text-coral">{tr("priority")} {item.priority}</div>
                <div className="mt-2 font-semibold text-ink">{tr(item.title)}</div>
                <div className="mt-3 text-slate-600">{tr(item.reason)}</div>
              </Link>
            ))}
          </div>
        </Card>
      ) : null}

      {listeningTrend ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Listening contribution")}</div>
            <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open progress")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Average score")}: <span className="font-semibold text-ink">{listeningTrend.averageScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent attempts")}: <span className="font-semibold text-ink">{listeningTrend.recentAttempts}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              Transcript support: <span className="font-semibold text-ink">{listeningTrend.transcriptSupportRate}%</span>
            </div>
          </div>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Recent timeline")}</div>
            <div className="flex flex-wrap gap-2">
              <Link to={routes.progress} className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink">
                {tr("Lessons")}
              </Link>
              <Link to={routes.speaking} className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink">
                {tr("Speaking")}
              </Link>
              <Link to={routes.pronunciation} className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink">
                {tr("Pronunciation")}
              </Link>
            </div>
          </div>
          {activityError ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {activityError}
            </div>
          ) : null}
          {recentEvents.length === 0 ? (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Activity feed will populate after the first lesson completion or speaking attempt.")}
            </div>
          ) : (
            recentEvents.map((event) => (
              <Link key={event.id} to={event.route} className="block rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{tr(event.title)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(event.meta)}</div>
                  </div>
                  <div className="text-xs text-slate-500">{event.createdAt ? formatDateTime(event.createdAt) : tr("current session")}</div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{tr(event.detail)}</div>
              </Link>
            ))
          )}
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-lg font-semibold text-ink">{tr("Top mistake patterns")}</div>
              <Link to={routes.mistakes} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                {tr("Open all")}
              </Link>
            </div>
            {topMistakes.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                {tr("Mistake analytics will appear here after lesson completion and correction extraction.")}
              </div>
            ) : (
              topMistakes.map((mistake) => (
                <div key={mistake.id} className="rounded-2xl bg-white/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-ink">{tr(mistake.subtype)}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                        {tt(mistake.category)} • {tt(mistake.sourceModule)}
                      </div>
                    </div>
                    <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">{tr("repeats")} {mistake.repetitionCount}</div>
                  </div>
                  <div className="mt-3 text-sm text-slate-600">{tr(mistake.explanation)}</div>
                </div>
              ))
            )}
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Quick jumps")}</div>
            <Link to={routes.lessonResults} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Current lesson result")}</div>
              <div className="mt-2 text-sm text-slate-600">{tr("Open the latest in-session result screen if a recent completion happened.")}</div>
            </Link>
            <Link to={routes.progress} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Progress deep dive")}</div>
              <div className="mt-2 text-sm text-slate-600">{tr("See skill balances, daily goal and recent lesson history.")}</div>
            </Link>
            <Link to={routes.speaking} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Speaking practice log")}</div>
              <div className="mt-2 text-sm text-slate-600">{tr("Continue voice training and review speaking attempts in detail.")}</div>
            </Link>
            <Link to={routes.pronunciation} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Pronunciation trend view")}</div>
              <div className="mt-2 text-sm text-slate-600">{tr("Review recurring weak sounds and pronunciation history outside the lab context.")}</div>
            </Link>
            <Link to={routes.vocabulary} className="block rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr("Vocabulary hub")}</div>
              <div className="mt-2 text-sm text-slate-600">{tr("Review due cards, recent vocabulary activity and queue balance.")}</div>
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
}

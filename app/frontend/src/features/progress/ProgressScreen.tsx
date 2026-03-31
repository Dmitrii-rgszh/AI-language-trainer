import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import type { ListeningAttempt, ListeningTrend, PronunciationTrend, SpeakingAttempt } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";
import { SectionHeading } from "../../shared/ui/SectionHeading";

function resolutionTone(status: string) {
  if (status === "stabilizing") {
    return "bg-mint/40 text-ink";
  }
  if (status === "recovering") {
    return "bg-sand text-ink";
  }
  return "bg-rose-100 text-rose-700";
}

export function ProgressScreen() {
  const { tr, tt, tl, formatDate, formatDateTime, formatDays } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const progress = useAppStore((state) => state.progress);
  const diagnosticRoadmap = useAppStore((state) => state.diagnosticRoadmap);
  const startDiagnosticCheckpoint = useAppStore((state) => state.startDiagnosticCheckpoint);
  const [speakingAttempts, setSpeakingAttempts] = useState<SpeakingAttempt[]>([]);
  const [pronunciationTrend, setPronunciationTrend] = useState<PronunciationTrend | null>(null);
  const [listeningAttempts, setListeningAttempts] = useState<ListeningAttempt[]>([]);
  const [listeningTrend, setListeningTrend] = useState<ListeningTrend | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    async function loadActivityContext() {
      try {
        const [attempts, trend, nextListeningAttempts, nextListeningTrend] = await Promise.all([
          apiClient.getSpeakingAttempts(),
          apiClient.getPronunciationTrends(),
          apiClient.getListeningHistory(),
          apiClient.getListeningTrends(),
        ]);
        if (isMounted) {
          setSpeakingAttempts(attempts);
          setPronunciationTrend(trend);
          setListeningAttempts(nextListeningAttempts);
          setListeningTrend(nextListeningTrend);
          setActivityError(null);
        }
      } catch (error) {
        if (isMounted) {
          setActivityError(error instanceof Error ? error.message : "Failed to load speaking or pronunciation activity");
        }
      }
    }

    void loadActivityContext();

    return () => {
      isMounted = false;
    };
  }, []);

  if (!progress) {
    return <Card>{tr("Подгружаю progress...")}</Card>;
  }

  const dailyGoalProgress = Math.min(
    100,
    Math.round((progress.minutesCompletedToday / Math.max(progress.dailyGoalMinutes, 1)) * 100),
  );
  const averageLessonScore =
    progress.history.length > 0
      ? Math.round(progress.history.reduce((total, item) => total + item.score, 0) / progress.history.length)
      : 0;
  const mostRecentLesson = progress.history[0] ?? null;
  const recentSpeakingAttempts = speakingAttempts.slice(0, 4);

  const handleStartCheckpoint = async () => {
    await startDiagnosticCheckpoint();
    navigate(routes.lessonRunner);
  };

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Progress")}
        title={tr("Skill Progress")}
        description={tr(
          "В этом модуле уже есть skill scores, streak, daily goal и lesson history. Следующий шаг — добавить реальные charts и persistence layer.",
        )}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ScoreBadge label={tr("Grammar")} score={progress.grammarScore} />
        <ScoreBadge label={tr("Speaking")} score={progress.speakingScore} />
        <ScoreBadge label={tr("Pronunciation")} score={progress.pronunciationScore} />
        <ScoreBadge label={tr("Writing")} score={progress.writingScore} />
      </div>

      {diagnosticRoadmap ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
          <Card className="space-y-4">
            <div className="text-lg font-semibold text-ink">{tr("Level diagnostic")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr(diagnosticRoadmap.summary)}</div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {tr("Declared")}: <span className="font-semibold text-ink">{diagnosticRoadmap.declaredCurrentLevel}</span>
              </div>
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {tr("Estimated")}: <span className="font-semibold text-ink">{diagnosticRoadmap.estimatedLevel}</span>
              </div>
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {tr("Target")}: <span className="font-semibold text-ink">{diagnosticRoadmap.targetLevel}</span>
              </div>
            </div>
            <div className="text-sm text-slate-600">
              {tr("Overall score")}: {diagnosticRoadmap.overallScore}. {tr("Weakest skills")}:{" "}
              {tl(diagnosticRoadmap.weakestSkills)}.
            </div>
            <Button onClick={() => void handleStartCheckpoint()}>{tr("Run diagnostic checkpoint")}</Button>
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Roadmap milestones")}</div>
            {diagnosticRoadmap.milestones.map((milestone) => (
              <div key={milestone.level} className="rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{milestone.level}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(milestone.status)}</div>
                  </div>
                  <div className="text-sm text-slate-600">{milestone.readiness}% {tr("ready")}</div>
                </div>
                <div className="mt-3 h-3 overflow-hidden rounded-full bg-sand">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${milestone.readiness}%` }} />
                </div>
                <div className="mt-3 text-sm text-slate-600">{tr(milestone.description)}</div>
                <div className="mt-3 text-xs uppercase tracking-[0.14em] text-slate-500">
                  {tr("Focus")}: {tl(milestone.focusSkills)}
                </div>
              </div>
            ))}
          </Card>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Daily goal")}</div>
          <div className="text-3xl font-semibold text-ink">
            {progress.minutesCompletedToday}/{progress.dailyGoalMinutes} min
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-sand">
            <div className="h-full rounded-full bg-accent" style={{ width: `${dailyGoalProgress}%` }} />
          </div>
          <div className="text-sm text-slate-600">{tr("Today completion")}: {dailyGoalProgress}%</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Consistency")}</div>
          <div className="text-3xl font-semibold text-ink">{formatDays(progress.streak)}</div>
          <div className="text-sm text-slate-600">{tr("Current streak across active learning days.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Average lesson score")}</div>
          <div className="text-3xl font-semibold text-ink">{averageLessonScore}</div>
          <div className="text-sm text-slate-600">
            {tr("Based on")} {progress.history.length}{" "}
            {tr(progress.history.length === 1 ? "completed lesson" : "completed lessons")}.
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Learning balance")}</div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Listening score")}: <span className="font-semibold text-ink">{progress.listeningScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Profession score")}: <span className="font-semibold text-ink">{progress.professionScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Regulation score")}: <span className="font-semibold text-ink">{progress.regulationScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent lessons")}: <span className="font-semibold text-ink">{progress.history.length}</span>
            </div>
          </div>
          </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Recent highlight")}</div>
          {mostRecentLesson ? (
            <div className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(mostRecentLesson.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                    {tt(mostRecentLesson.lessonType)}
                  </div>
                </div>
                <div className="text-sm text-slate-600">{tr("Score")} {mostRecentLesson.score}</div>
              </div>
              <div className="mt-3 text-sm text-slate-600">
                {tr("Last completed at")} {formatDate(mostRecentLesson.completedAt)}.
              </div>
            </div>
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("First completed lesson will appear here as soon as history starts filling up.")}
            </div>
          )}
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Pronunciation contribution")}</div>
          {pronunciationTrend ? (
            <>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                  {tr("Average score")}: <span className="font-semibold text-ink">{pronunciationTrend.averageScore}</span>
                </div>
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                  {tr("Recent checks")}: <span className="font-semibold text-ink">{pronunciationTrend.recentAttempts}</span>
                </div>
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                  {tr("Pronunciation")} score: <span className="font-semibold text-ink">{progress.pronunciationScore}</span>
                </div>
              </div>
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {pronunciationTrend.weakestSounds.length > 0
                  ? `${tr("Recurring weak sounds")}: ${pronunciationTrend.weakestSounds
                      .map((item) => `${item.label} (${item.occurrences}x)`)
                      .join(", ")}.`
                  : tr("No repeating weak sound pattern detected yet.")}
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {pronunciationTrend.weakestWords.length > 0
                  ? `${tr("Recurring weak words")}: ${pronunciationTrend.weakestWords
                      .map((item) => `${item.label} (${item.occurrences}x)`)
                      .join(", ")}.`
                  : tr("Weak-word trend will appear after repeated pronunciation checks.")}
              </div>
            </>
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Pronunciation trend data will appear here after the first saved audio checks.")}
            </div>
          )}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Roadmap reading")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Pronunciation now contributes through saved audio checks, not just a single lab verdict.")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("If repeating weak sounds stay visible here, your readiness to the next milestone should be treated as less stable even when grammar or writing move faster.")}</div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{tr("Use `Pronunciation Lab` to clear the top weak sound, then rerun a checkpoint to see whether the roadmap shifts upward more confidently.")}</div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Lesson history")}</div>
          {progress.history.map((item) => (
            <div key={item.id} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(item.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.lessonType)}</div>
                </div>
                <div className="text-sm text-slate-600">
                  {formatDate(item.completedAt)} • {tr("score")} {item.score}
                </div>
              </div>
            </div>
          ))}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Speaking activity")}</div>
          {activityError ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {activityError}
            </div>
          ) : null}
          {recentSpeakingAttempts.length === 0 ? (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Voice and text speaking attempts will appear here after the first practice session.")}
            </div>
          ) : (
            recentSpeakingAttempts.map((attempt) => (
              <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{tr(attempt.scenarioTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                      {tt(attempt.inputMode)} • {tr(attempt.feedbackSource)}
                    </div>
                  </div>
                  <div className="text-sm text-slate-600">{formatDateTime(attempt.createdAt)}</div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{attempt.feedbackSummary}</div>
              </div>
            ))
          )}
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Mistake to vocabulary contribution")}</div>
          {dashboard?.studyLoop?.vocabularyBacklinks?.length ? (
            <>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Some weak spots are already being recycled into vocabulary review, so the app is no longer treating them as isolated corrections.")}
              </div>
              {dashboard.studyLoop.vocabularyBacklinks.map((link) => (
                <div key={link.weakSpotTitle} className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  <div className="font-semibold text-ink">{tr(link.weakSpotTitle)}</div>
                  <div className="mt-2">
                    {link.dueCount} {tr("due")} and {link.activeCount} {tr("active")} vocabulary items now reinforce this weak spot.
                  </div>
                  <div className="mt-2">Examples: {link.exampleWords.join(", ")}.</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.12em] text-slate-500">
                    {tr("sources")}: {link.sourceModules.map((item) => tt(item)).join(", ")}
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Once weak spots start converting into vocabulary review, the closed loop will appear here.")}
            </div>
          )}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Recovering weak spots")}</div>
          {dashboard?.studyLoop?.mistakeResolution?.length ? (
            dashboard.studyLoop.mistakeResolution.map((item) => (
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
                  {tr("Repeats")} {item.repetitionCount}. {tr("Last seen")} {formatDays(item.lastSeenDaysAgo)} ago.
                </div>
                <div className="mt-2 text-sm text-slate-600">
                  {tr("Linked vocabulary support")}: {item.linkedVocabularyCount}.
                </div>
                <div className="mt-3 rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">{tr(item.resolutionHint)}</div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Recovery visibility will appear once weak spots have enough history to show whether they are staying active or starting to settle down.")}
            </div>
          )}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Listening activity")}</div>
          {listeningTrend ? (
            <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {tr("Average score")} {listeningTrend.averageScore}. Transcript support used in {listeningTrend.transcriptSupportRate}% of recent attempts.
            </div>
          ) : null}
          {listeningAttempts.length === 0 ? (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Listening attempts will appear here after completing audio-first lesson blocks.")}
            </div>
          ) : (
            listeningAttempts.slice(0, 4).map((attempt) => (
              <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{tr(attempt.lessonTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                      {attempt.promptLabel ? tr(attempt.promptLabel) : tr(attempt.blockTitle)}
                    </div>
                  </div>
                  <div className="text-sm text-slate-600">{tr("score")} {attempt.score}</div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{attempt.answerSummary}</div>
                <div className="mt-2 text-xs text-slate-500">
                  {attempt.usedTranscriptSupport ? tr("Transcript support used") : tr("Audio-first answer")}
                </div>
              </div>
            ))
          )}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Listening trend reading")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Listening now has saved attempt memory, not just one score inside the roadmap.")}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {listeningTrend?.weakestPrompts.length
              ? `${tr("Recurring weak prompts")}: ${listeningTrend.weakestPrompts
                  .map((item) => `${item.label} (${item.occurrences}x)`)
                  .join(", ")}.`
              : tr("No recurring weak listening prompt has emerged yet.")}
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{tr("Use transcript support rate as a confidence signal: lower support over time means listening is stabilizing.")}</div>
        </Card>
      </div>
    </div>
  );
}

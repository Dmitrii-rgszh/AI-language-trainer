import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../shared/api/client";
import { useLocale } from "../../shared/i18n/useLocale";
import type { AITextFeedback, WritingAttempt } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function WritingScreen() {
  const { tr, formatDateTime } = useLocale();
  const writingTask = useAppStore((state) => state.writingTask);
  const [draft, setDraft] = useState(
    "Hello team, I am writing to share that our onboarding workshop was helpful and people feels more confident after the session.",
  );
  const [feedback, setFeedback] = useState<AITextFeedback | null>(null);
  const [attempts, setAttempts] = useState<WritingAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);

  useEffect(() => {
    void loadAttempts();
  }, []);

  if (!writingTask) {
    return <Card>{tr("Подгружаю writing task...")}</Card>;
  }

  const activeTask = writingTask;

  async function loadAttempts() {
    setIsHistoryLoading(true);
    try {
      const history = await apiClient.getWritingAttempts();
      setAttempts(history);
    } catch (historyError) {
      setError(historyError instanceof Error ? historyError.message : "Writing history failed");
    } finally {
      setIsHistoryLoading(false);
    }
  }

  async function requestReview() {
    setIsLoading(true);
    setError(null);

    try {
      const nextFeedback = await apiClient.reviewWriting({
        taskId: activeTask.id,
        draft,
        feedbackLanguage: "ru",
      });
      setFeedback(nextFeedback);
      await loadAttempts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Writing review failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function playFeedbackVoice(targetFeedback?: Pick<AITextFeedback, "voiceText" | "voiceLanguage">) {
    const feedbackToPlay = targetFeedback ?? feedback;
    if (!feedbackToPlay) {
      return;
    }

    setIsPlaying(true);
    setError(null);

    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text: feedbackToPlay.voiceText,
        language: feedbackToPlay.voiceLanguage,
        style: "coach",
      });

      if (currentAudioUrlRef.current) {
        URL.revokeObjectURL(currentAudioUrlRef.current);
      }

      const audioUrl = URL.createObjectURL(audioBlob);
      currentAudioUrlRef.current = audioUrl;

      if (!audioRef.current) {
        audioRef.current = new Audio();
      }

      audioRef.current.src = audioUrl;
      audioRef.current.onended = () => setIsPlaying(false);
      await audioRef.current.play();
    } catch (playbackError) {
      setIsPlaying(false);
      setError(playbackError instanceof Error ? playbackError.message : "Voice playback failed");
    }
  }

  function reuseAttempt(attempt: WritingAttempt) {
    setDraft(attempt.draft);
    setFeedback({
      source: attempt.feedbackSource,
      summary: attempt.feedbackSummary,
      voiceText: attempt.voiceText,
      voiceLanguage: attempt.voiceLanguage,
    });
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Writing Coach")}
        title={tr(activeTask.title)}
        description={tr(
          "Writing теперь уже не одноразовый review: черновики и feedback копятся в истории, удачные версии можно быстро переиспользовать, а повторяющиеся ошибки попадают в общую mistake map.",
        )}
      />

      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="space-y-4">
          <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">{activeTask.brief}</div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{tr("Tone")}: {activeTask.tone}</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {activeTask.checklist.map((item) => (
              <div key={item}>• {item}</div>
            ))}
          </div>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            className="min-h-52 w-full rounded-2xl border border-sand-dark/40 bg-white/80 p-4 text-sm leading-6 text-slate-700 outline-none transition focus:border-coral"
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void requestReview()}
              disabled={isLoading}
              className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-ink/85 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isLoading ? tr("Reviewing...") : tr("Get AI review")}
            </button>
            <button
              type="button"
              onClick={() => void playFeedbackVoice()}
              disabled={!feedback || isPlaying}
              className="rounded-full bg-coral px-4 py-2 text-sm font-semibold text-white transition hover:bg-coral/85 disabled:cursor-not-allowed disabled:bg-slate-400"
            >
              {isPlaying ? tr("Playing...") : tr("Play tutor voice")}
            </button>
            <button
              type="button"
              onClick={() => {
                setDraft("");
                setFeedback(null);
              }}
              className="rounded-full border border-ink/15 bg-white/70 px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink/35"
            >
              {tr("Clear draft")}
            </button>
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="space-y-4">
            <div className="text-lg font-semibold text-ink">{tr("AI writing review")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
              {feedback?.summary ?? activeTask.improvedVersionPreview}
            </div>
            <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {feedback ? `${tr("Feedback source")}: ${tr(feedback.source)}` : tr("Сначала отправь черновик на review.")}
            </div>
            <div className="rounded-2xl bg-mint/30 p-4 text-sm text-slate-700">
              {tr("Writing corrections now feed the same adaptive mistake map as lessons and speaking practice, so repeated issues can change the next recovery focus.")}
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Stronger corrected words and phrase patterns from this draft can now move into the shared vocabulary review queue too.")}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{tr("Draft history")}</div>
                <div className="text-sm text-slate-600">{tr("Последние версии и feedback теперь можно переиспользовать.")}</div>
              </div>
              <div className="rounded-full bg-sand/80 px-3 py-1 text-xs font-semibold text-slate-700">
                {isHistoryLoading ? tr("Loading...") : `${attempts.length} ${tr("saved")}`}
              </div>
            </div>

            {attempts.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                {tr("После первого review здесь появятся сохранённые черновики и tutor feedback.")}
              </div>
            ) : (
              <div className="space-y-3">
                {attempts.map((attempt) => (
                  <div key={attempt.id} className="rounded-2xl border border-ink/10 bg-white/70 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-ink">{tr(attempt.taskTitle)}</div>
                        <div className="text-xs text-slate-500">
                          {formatDateTime(attempt.createdAt)}
                        </div>
                      </div>
                      <div className="rounded-full bg-sand/80 px-3 py-1 text-xs font-semibold text-slate-700">
                        {attempt.feedbackSource === "ai" ? tr("AI-backed") : tr("Fallback review")}
                      </div>
                    </div>
                    <div className="mt-3 rounded-2xl bg-white p-3 text-sm leading-6 text-slate-700">{attempt.draft}</div>
                    <div className="mt-3 rounded-2xl bg-mint/30 p-3 text-sm leading-6 text-slate-700">
                      {attempt.feedbackSummary}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => reuseAttempt(attempt)}
                        className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-ink/85"
                      >
                        {tr("Reuse draft")}
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          void playFeedbackVoice({
                            voiceText: attempt.voiceText,
                            voiceLanguage: attempt.voiceLanguage,
                          })
                        }
                        disabled={isPlaying}
                        className="rounded-full border border-coral/40 bg-white px-4 py-2 text-sm font-semibold text-coral transition hover:border-coral disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
                      >
                        {tr("Play again")}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

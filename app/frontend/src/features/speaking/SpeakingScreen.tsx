import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../shared/api/client";
import { useLocale } from "../../shared/i18n/useLocale";
import type { AITextFeedback, SpeakingAttempt } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function SpeakingScreen() {
  const { tr, tt, formatDateTime } = useLocale();
  const scenarios = useAppStore((state) => state.speakingScenarios);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(scenarios[0]?.id ?? null);
  const [transcript, setTranscript] = useState(
    "I have worked with sales teams across several product launches, and recently I have focused more on feedback design for managers.",
  );
  const [feedback, setFeedback] = useState<AITextFeedback | null>(null);
  const [attempts, setAttempts] = useState<SpeakingAttempt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [autoplayTutorVoice, setAutoplayTutorVoice] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  const activeScenario = scenarios.find((scenario) => scenario.id === activeScenarioId) ?? scenarios[0];
  const recentAttempts = attempts.slice(0, 5);
  const voiceAttempts = attempts.filter((attempt) => attempt.inputMode === "voice");
  const aiAttempts = attempts.filter((attempt) => attempt.feedbackSource === "ai");
  const averageTranscriptWords =
    attempts.length > 0
      ? Math.round(
          attempts.reduce((total, attempt) => total + attempt.transcript.split(/\s+/).filter(Boolean).length, 0) /
            attempts.length,
        )
      : 0;

  useEffect(() => {
    void loadAttempts();
  }, []);

  async function loadAttempts() {
    try {
      const history = await apiClient.getSpeakingAttempts();
      setAttempts(history);
    } catch (historyError) {
      setError(historyError instanceof Error ? historyError.message : "Failed to load speaking history");
    }
  }

  async function requestFeedback() {
    if (!activeScenario) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const nextFeedback = await apiClient.getSpeakingFeedback({
        scenarioId: activeScenario.id,
        transcript,
        feedbackLanguage: "ru",
      });
      setFeedback(nextFeedback);
      await loadAttempts();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Speaking feedback failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function startRecording() {
    if (isRecording) {
      return;
    }

    setError(null);
    recordedChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };
      mediaRecorder.start();
      setIsRecording(true);
    } catch (recordingError) {
      setError(recordingError instanceof Error ? recordingError.message : "Microphone access failed");
    }
  }

  async function stopRecordingAndAnalyze() {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || !activeScenario) {
      return;
    }

    setIsLoading(true);
    setError(null);

    const recordedBlob = await new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        resolve(new Blob(recordedChunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" }));
      };
      mediaRecorder.stop();
    });

    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);

    try {
      const response = await apiClient.getSpeakingVoiceFeedback({
        scenarioId: activeScenario.id,
        audio: recordedBlob,
        feedbackLanguage: "ru",
      });
      setTranscript(response.transcript);
      setFeedback(response.feedback);
      await loadAttempts();
      if (autoplayTutorVoice) {
        await playFeedbackVoice(response.feedback);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Voice feedback failed");
    } finally {
      setIsLoading(false);
    }
  }

  async function playFeedbackVoice(feedbackToPlay?: AITextFeedback) {
    const targetFeedback = feedbackToPlay ?? feedback;
    if (!targetFeedback) {
      return;
    }

    setIsPlaying(true);
    setError(null);

    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text: targetFeedback.voiceText,
        language: targetFeedback.voiceLanguage,
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

  function reuseAttemptTranscript(attempt: SpeakingAttempt) {
    setActiveScenarioId(attempt.scenarioId);
    setTranscript(attempt.transcript);
    setFeedback({
      source: attempt.feedbackSource,
      summary: attempt.feedbackSummary,
      voiceText: attempt.voiceText,
      voiceLanguage: attempt.voiceLanguage,
    });
    setError(null);
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Speaking Partner")}
        title={tr("Speaking Studio")}
        description={tr(
          "Теперь voice loop уже замкнут: запись голоса, transcript, AI feedback, autoplay tutor voice и история попыток. Повторяющиеся ошибки отсюда тоже попадают в общий adaptive loop.",
        )}
      />

      {error ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          {scenarios.map((scenario) => (
            <Card key={scenario.id} className="space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-lg font-semibold text-ink">{tr(scenario.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(scenario.mode)}</div>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveScenarioId(scenario.id)}
                  className={`rounded-2xl px-3 py-2 text-xs ${
                    activeScenarioId === scenario.id ? "bg-ink text-white" : "bg-white/70 text-slate-600"
                  }`}
                >
                  {activeScenarioId === scenario.id ? tr("Active") : tr("Use")}
                </button>
              </div>

              <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">{scenario.prompt}</div>
              <div className="text-sm text-slate-600">
                {tr("Feedback focus")}: {tr(scenario.feedbackHint)}
              </div>
            </Card>
          ))}
        </div>

        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="space-y-2">
              <div className="text-xs uppercase tracking-[0.16em] text-coral">{tr("Total Attempts")}</div>
              <div className="text-3xl font-semibold text-ink">{attempts.length}</div>
              <div className="text-sm text-slate-600">{tr("Все speaking попытки, включая voice и text input.")}</div>
            </Card>
            <Card className="space-y-2">
              <div className="text-xs uppercase tracking-[0.16em] text-coral">{tr("Voice Ratio")}</div>
              <div className="text-3xl font-semibold text-ink">
                {attempts.length > 0 ? Math.round((voiceAttempts.length / attempts.length) * 100) : 0}%
              </div>
              <div className="text-sm text-slate-600">{tr("Доля попыток, где ты реально говорил голосом.")}</div>
            </Card>
            <Card className="space-y-2">
              <div className="text-xs uppercase tracking-[0.16em] text-coral">{tr("Avg Length")}</div>
              <div className="text-3xl font-semibold text-ink">{averageTranscriptWords}</div>
              <div className="text-sm text-slate-600">{tr("Средняя длина transcript в словах.")}</div>
            </Card>
          </div>

          <Card className="space-y-4">
            <div className="text-lg font-semibold text-ink">{tr("Live transcript")}</div>
            <textarea
              value={transcript}
              onChange={(event) => setTranscript(event.target.value)}
              className="min-h-40 w-full rounded-2xl border border-sand-dark/40 bg-white/80 p-4 text-sm leading-6 text-slate-700 outline-none transition focus:border-coral"
            />
            <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {tr("Goal")}: {activeScenario?.goal ? tr(activeScenario.goal) : tr("Выбери speaking scenario")}
            </div>
            <label className="flex items-center gap-3 rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={autoplayTutorVoice}
                onChange={(event) => setAutoplayTutorVoice(event.target.checked)}
              />
              {tr("Autoplay tutor voice after voice analysis")}
            </label>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void requestFeedback()}
                disabled={isLoading || !activeScenario}
                className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-ink/85 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isLoading ? tr("Analyzing...") : tr("Get AI feedback")}
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
                onClick={() => void (isRecording ? stopRecordingAndAnalyze() : startRecording())}
                disabled={isLoading || !activeScenario}
                className="rounded-full bg-slate-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-600 disabled:cursor-not-allowed disabled:bg-slate-400"
              >
                {isRecording ? tr("Stop & analyze voice") : tr("Record voice")}
              </button>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
              {feedback?.summary ?? tr("Здесь появится живой speaking feedback от модели.")}
            </div>
            <div className="rounded-2xl bg-mint/30 p-4 text-sm text-slate-700">
              {tr("Repeated corrections from speaking review are added to the shared mistake map and can reshape the next adaptive recommendation.")}
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Useful corrected words and phrases from this review can also appear later in the vocabulary repetition loop.")}
            </div>
          </Card>

          <Card className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="text-lg font-semibold text-ink">{tr("Recent attempts")}</div>
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
                {tr("AI-backed")}: {aiAttempts.length}/{attempts.length || 0}
              </div>
            </div>
            {attempts.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                {tr("История пока пустая. Сделай первую speaking попытку.")}
              </div>
            ) : (
              <div className="space-y-3">
                {recentAttempts.map((attempt) => (
                  <div key={attempt.id} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-ink">{tr(attempt.scenarioTitle)}</div>
                      <div className="text-xs uppercase tracking-[0.16em] text-coral">
                        {tt(attempt.inputMode)} | {tr(attempt.feedbackSource)}
                      </div>
                    </div>
                    <div className="mt-2 text-slate-600">{attempt.transcript}</div>
                    <div className="mt-3 rounded-2xl bg-sand/70 p-3">{attempt.feedbackSummary}</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          void playFeedbackVoice({
                            source: attempt.feedbackSource,
                            summary: attempt.feedbackSummary,
                            voiceText: attempt.voiceText,
                            voiceLanguage: attempt.voiceLanguage,
                          })
                        }
                        className="rounded-full bg-ink px-3 py-1 text-xs font-semibold text-white transition hover:bg-ink/85"
                      >
                        {tr("Play again")}
                      </button>
                      <button
                        type="button"
                        onClick={() => reuseAttemptTranscript(attempt)}
                        className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
                      >
                        {tr("Reuse transcript")}
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

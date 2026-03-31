import { useEffect, useRef, useState } from "react";
import { apiClient } from "../../shared/api/client";
import { useLocale } from "../../shared/i18n/useLocale";
import type { PronunciationAssessment, PronunciationAttempt, PronunciationTrend } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function PronunciationScreen() {
  const { tr, formatDateTime } = useLocale();
  const drills = useAppStore((state) => state.pronunciationDrills);
  const providers = useAppStore((state) => state.providers);
  const [activePhrase, setActivePhrase] = useState<string | null>(null);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  const [assessment, setAssessment] = useState<PronunciationAssessment | null>(null);
  const [assessmentTarget, setAssessmentTarget] = useState<string | null>(null);
  const [assessmentDrillId, setAssessmentDrillId] = useState<string | null>(null);
  const [assessmentSoundFocus, setAssessmentSoundFocus] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isAssessing, setIsAssessing] = useState(false);
  const [attempts, setAttempts] = useState<PronunciationAttempt[]>([]);
  const [trends, setTrends] = useState<PronunciationTrend | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const ttsProvider = providers.find((provider) => provider.type === "tts");
  const scoringProvider = providers.find((provider) => provider.type === "scoring");

  async function loadPronunciationHistory() {
    try {
      const [nextAttempts, nextTrends] = await Promise.all([
        apiClient.getPronunciationAttempts(),
        apiClient.getPronunciationTrends(),
      ]);
      setAttempts(nextAttempts);
      setTrends(nextTrends);
    } catch (error) {
      setPlaybackError(error instanceof Error ? error.message : "Pronunciation history could not be loaded");
    }
  }

  useEffect(() => {
    void loadPronunciationHistory();
  }, []);

  async function playPhrase(phrase: string) {
    setPlaybackError(null);
    setActivePhrase(phrase);

    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text: phrase,
        language: "en",
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
      audioRef.current.onended = () => setActivePhrase(null);
      await audioRef.current.play();
    } catch (error) {
      setActivePhrase(null);
      setPlaybackError(error instanceof Error ? error.message : "Voice playback failed");
    }
  }

  async function startRecording(targetPhrase: string, drillId: string, soundFocus: string) {
    if (isRecording) {
      return;
    }

    setPlaybackError(null);
    setAssessmentTarget(targetPhrase);
    setAssessmentDrillId(drillId);
    setAssessmentSoundFocus(soundFocus);
    setAssessment(null);
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
    } catch (error) {
      setPlaybackError(error instanceof Error ? error.message : "Microphone access failed");
    }
  }

  async function stopRecordingAndAssess() {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || !assessmentTarget) {
      return;
    }

    setIsAssessing(true);
    setPlaybackError(null);

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
      const result = await apiClient.assessPronunciation({
        targetText: assessmentTarget,
        drillId: assessmentDrillId ?? undefined,
        soundFocus: assessmentSoundFocus ?? undefined,
        audio: recordedBlob,
      });
      setAssessment(result);
      await loadPronunciationHistory();
    } catch (error) {
      setPlaybackError(error instanceof Error ? error.message : "Pronunciation assessment failed");
    } finally {
      setIsAssessing(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Pronunciation Coach")}
        title={tr("Pronunciation Lab")}
        description={tr("Теперь lab хранит историю попыток и показывает повторяющиеся слабые звуки и слова, а не только последний verdict.")}
      />

      {playbackError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {playbackError}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Voice playback")}</div>
          <div className="text-3xl font-semibold text-ink">{tr(ttsProvider?.status ?? "offline")}</div>
          <div className="text-sm text-slate-600">{tr(ttsProvider?.details ?? "No TTS provider detected.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Scoring layer")}</div>
          <div className="text-3xl font-semibold text-ink">{tr(scoringProvider?.status ?? "offline")}</div>
          <div className="text-sm text-slate-600">
            {tr(scoringProvider?.details ?? "Pronunciation scoring is not fully wired yet.")}
          </div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Practice mode")}</div>
          <div className="text-3xl font-semibold text-ink">{drills.length}</div>
          <div className="text-sm text-slate-600">{tr("Drill packs available for immediate listen-and-repeat practice.")}</div>
        </Card>
      </div>

      {trends ? (
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="space-y-3">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Recent attempts")}</div>
            <div className="text-3xl font-semibold text-ink">{trends.recentAttempts}</div>
            <div className="text-sm text-slate-600">{tr("Pronunciation checks saved in rolling history.")}</div>
          </Card>
          <Card className="space-y-3">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Average score")}</div>
            <div className="text-3xl font-semibold text-ink">{trends.averageScore}</div>
            <div className="text-sm text-slate-600">{tr("Recent pronunciation average across saved attempts.")}</div>
          </Card>
          <Card className="space-y-3">
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Weakest sound trend")}</div>
            <div className="text-3xl font-semibold text-ink">{trends.weakestSounds[0]?.label ?? tr("stable")}</div>
            <div className="text-sm text-slate-600">
              {trends.weakestSounds[0]
                ? `${tr("Seen")} ${trends.weakestSounds[0].occurrences} ${tr("times in recent checks.")}`
                : tr("No repeating weak sound pattern detected yet.")}
            </div>
          </Card>
        </div>
      ) : null}

      {assessment ? (
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Latest pronunciation check")}</div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Target")}: <span className="font-semibold text-ink">{assessment.targetText}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Transcript")}: <span className="font-semibold text-ink">{assessment.transcript}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Score")}: <span className="font-semibold text-ink">{assessment.score}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{assessment.feedback}</div>
          {assessment.weakestWords.length > 0 ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              {tr("Priority fix words")}: {assessment.weakestWords.join(", ")}
            </div>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Matched tokens")}: {assessment.matchedTokens.join(", ") || tr("none")}
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Missed tokens")}: {assessment.missedTokens.join(", ") || tr("none")}
            </div>
          </div>
          {assessment.focusAssessments.length > 0 ? (
            <div className="space-y-3">
              <div className="text-sm font-semibold text-ink">{tr("Sound focus diagnostics")}</div>
              <div className="grid gap-3 md:grid-cols-2">
                {assessment.focusAssessments.map((item) => (
                  <div key={item.focus} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                    <div className="font-semibold text-ink">
                      {item.focus} · {item.status}
                    </div>
                    <div className="mt-2">{item.note}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {assessment.wordAssessments.length > 0 ? (
            <div className="space-y-3">
              <div className="text-sm font-semibold text-ink">{tr("Word-level assessment")}</div>
              <div className="grid gap-3 md:grid-cols-2">
                {assessment.wordAssessments.map((item) => (
                  <div key={item.targetWord} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="font-semibold text-ink">{item.targetWord}</div>
                      <div>{item.score}/100</div>
                    </div>
                    <div className="mt-2">{tr("Heard")}: {item.heardWord ?? tr("not detected")}</div>
                    <div className="mt-2 text-xs uppercase tracking-[0.14em] text-coral">{item.status}</div>
                    <div className="mt-2">{item.note}</div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>
      ) : null}

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Weakest sound trends")}</div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Recurring weak sounds")}</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {trends?.weakestSounds.length ? (
                trends.weakestSounds.map((item) => (
                  <div key={item.label} className="flex items-center justify-between gap-3">
                    <span>{item.label}</span>
                    <span>{item.occurrences}x</span>
                  </div>
                ))
              ) : (
                <div>{tr("No repeating sound issue yet.")}</div>
              )}
            </div>
          </div>
          <div className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Recurring weak words")}</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {trends?.weakestWords.length ? (
                trends.weakestWords.map((item) => (
                  <div key={item.label} className="flex items-center justify-between gap-3">
                    <span>{item.label}</span>
                    <span>{item.occurrences}x</span>
                  </div>
                ))
              ) : (
                <div>{tr("No repeating weak word yet.")}</div>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("How to use this lab")}</div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            1. Play each phrase and listen to rhythm, stress and vowel length.
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            2. Record your version and compare recurring weak words or sounds over time.
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            3. Use those trends before speaking practice so the same sound issue stops repeating.
          </div>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {drills.map((drill) => (
          <Card key={drill.id} className="space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{drill.title}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{drill.sound}</div>
              </div>
              <div className="rounded-2xl bg-white/70 px-3 py-2 text-xs text-slate-600">{drill.difficulty}</div>
            </div>

            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{drill.focus}</div>
            <div className="space-y-2 rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {drill.phrases.map((phrase) => (
                <div key={phrase} className="flex items-center justify-between gap-3 rounded-2xl bg-white/50 px-3 py-2">
                  <span>{phrase}</span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void playPhrase(phrase)}
                      className="rounded-full bg-ink px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-ink/85"
                      >
                      {activePhrase === phrase ? tr("Playing") : tr("Play")}
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        void (
                          isRecording && assessmentTarget === phrase
                            ? stopRecordingAndAssess()
                            : startRecording(phrase, drill.id, drill.sound)
                        )
                      }
                      disabled={isAssessing}
                      className="rounded-full bg-coral px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-coral/85 disabled:opacity-60"
                    >
                      {isRecording && assessmentTarget === phrase
                        ? tr("Stop & score")
                        : isAssessing && assessmentTarget === phrase
                          ? tr("Scoring...")
                          : tr("Record")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {attempts.length > 0 ? (
        <Card className="space-y-4">
          <div className="text-lg font-semibold text-ink">{tr("Recent pronunciation history")}</div>
          <div className="space-y-3">
            {attempts.map((attempt) => (
              <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-ink">{attempt.targetText}</div>
                  <div className="text-sm text-slate-600">{attempt.score}/100</div>
                </div>
                <div className="mt-2 text-sm text-slate-600">
                  {attempt.drillTitle ? tr(attempt.drillTitle) : tr("Custom phrase")}
                  {attempt.soundFocus ? ` · ${tr("focus")} ${attempt.soundFocus}` : ""}
                  {attempt.createdAt ? ` · ${formatDateTime(attempt.createdAt)}` : ""}
                </div>
                <div className="mt-3 text-sm text-slate-700">Transcript: {attempt.transcript}</div>
                <div className="mt-2 text-sm text-slate-600">{attempt.feedback}</div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs uppercase tracking-[0.14em] text-coral">
                  {attempt.weakestWords.map((word) => (
                    <span key={`${attempt.id}-${word}`} className="rounded-full bg-sand px-3 py-1 text-ink">
                      {tr("word")} {word}
                    </span>
                  ))}
                  {attempt.focusIssues.map((focus) => (
                    <span key={`${attempt.id}-${focus}`} className="rounded-full bg-white px-3 py-1 text-ink">
                      {tr("sound")} {focus}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}

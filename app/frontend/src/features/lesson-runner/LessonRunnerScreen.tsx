import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { LessonBlock } from "../../entities/lesson/model";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { LessonStepper } from "../../shared/ui/LessonStepper";
import { SectionHeading } from "../../shared/ui/SectionHeading";

function renderPayload(block: LessonBlock) {
  return Object.entries(block.payload)
    .filter(
      ([key]) =>
        !(
          block.blockType === "listening_block" &&
          ["transcript", "audio_asset_id", "audio_variants", "questions", "answer_key", "answerKey"].includes(key)
        ),
    )
    .map(([key, value]) => {
    if (Array.isArray(value)) {
      return (
        <div key={key} className="rounded-2xl bg-white/70 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{key}</div>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {value.map((item, index) => (
              <li key={`${block.id}-${index}`}>• {String(item)}</li>
            ))}
          </ul>
        </div>
      );
    }

    return (
      <div key={key} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
        <span className="font-semibold text-ink">{key}:</span> {String(value)}
      </div>
    );
    });
}

export function LessonRunnerScreen() {
  const { tr, tt } = useLocale();
  const lesson = useAppStore((state) => state.lesson);
  const selectedBlockIndex = useAppStore((state) => state.selectedBlockIndex);
  const blockResponses = useAppStore((state) => state.blockResponses);
  const setBlockResponse = useAppStore((state) => state.setBlockResponse);
  const setBlockScore = useAppStore((state) => state.setBlockScore);
  const listeningTranscriptReveals = useAppStore((state) => state.listeningTranscriptReveals);
  const markListeningTranscriptRevealed = useAppStore((state) => state.markListeningTranscriptRevealed);
  const saveActiveBlock = useAppStore((state) => state.saveActiveBlock);
  const previousBlock = useAppStore((state) => state.previousBlock);
  const nextBlock = useAppStore((state) => state.nextBlock);
  const completeLesson = useAppStore((state) => state.completeLesson);
  const startLesson = useAppStore((state) => state.startLesson);
  const resumeLessonRun = useAppStore((state) => state.resumeLessonRun);
  const discardLessonRun = useAppStore((state) => state.discardLessonRun);
  const restartLesson = useAppStore((state) => state.restartLesson);
  const navigate = useNavigate();
  const [isPlayingListening, setIsPlayingListening] = useState(false);
  const [showListeningTranscript, setShowListeningTranscript] = useState(false);
  const [selectedListeningVariantIndex, setSelectedListeningVariantIndex] = useState(0);
  const [isRecordingPronunciation, setIsRecordingPronunciation] = useState(false);
  const [isAssessingPronunciation, setIsAssessingPronunciation] = useState(false);
  const [runnerError, setRunnerError] = useState<string | null>(null);
  const [pronunciationTarget, setPronunciationTarget] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!lesson) {
      void resumeLessonRun();
    }
  }, [lesson, resumeLessonRun]);

  const activeBlock = lesson?.blocks[selectedBlockIndex];
  const transcriptWasRevealed = activeBlock ? (listeningTranscriptReveals[activeBlock.id] ?? false) : false;

  useEffect(() => {
    if (activeBlock) {
      setShowListeningTranscript(transcriptWasRevealed);
      setSelectedListeningVariantIndex(0);
    }
  }, [activeBlock?.id, transcriptWasRevealed]);

  if (!lesson) {
    return (
      <Card className="space-y-4">
        <div className="text-lg font-semibold text-ink">{tr("No lesson loaded yet")}</div>
        <div className="text-sm text-slate-600">
          {tr("Если незавершённый draft есть в backend, экран автоматически попробует его восстановить.")}
        </div>
        <Button onClick={() => void startLesson()}>{tr("Build recommended lesson")}</Button>
      </Card>
    );
  }

  const activeBlockCurrent = lesson.blocks[selectedBlockIndex] ?? lesson.blocks[0];
  const isLastBlock = selectedBlockIndex === lesson.blocks.length - 1;
  const listeningVariants = Array.isArray(activeBlockCurrent.payload.audio_variants)
    ? activeBlockCurrent.payload.audio_variants.filter(
        (
          item,
        ): item is {
          id?: string;
          label?: string;
          transcript?: string;
          questions?: Array<{ prompt?: string; acceptable_answers?: string[] }>;
        } => Boolean(item && typeof item === "object"),
      )
    : [];
  const selectedListeningVariant =
    listeningVariants[selectedListeningVariantIndex] ?? listeningVariants[0] ?? null;
  const listeningTranscript =
    selectedListeningVariant && typeof selectedListeningVariant.transcript === "string"
      ? selectedListeningVariant.transcript
      : typeof activeBlockCurrent.payload.transcript === "string"
        ? activeBlockCurrent.payload.transcript
        : null;
  const listeningQuestions =
    selectedListeningVariant && Array.isArray(selectedListeningVariant.questions)
      ? selectedListeningVariant.questions
          .filter(
            (
              item,
            ): item is {
              prompt: string;
              acceptable_answers?: string[];
            } => Boolean(item && typeof item === "object" && typeof item.prompt === "string"),
          )
          .map((item) => item.prompt)
      : Array.isArray(activeBlockCurrent.payload.questions)
        ? activeBlockCurrent.payload.questions.filter((item): item is string => typeof item === "string")
        : [];
  const pronunciationTargets = [
    ...((activeBlockCurrent?.payload.phraseDrills as string[] | undefined) ?? []),
    ...((activeBlockCurrent?.payload.phrase_drills as string[] | undefined) ?? []),
  ].filter(Boolean);

  async function playText(text: string, style: "neutral" | "coach" = "neutral") {
    if (!text) {
      return;
    }

    setRunnerError(null);
    setIsPlayingListening(true);
    try {
      const audioBlob = await apiClient.synthesizeSpeech({
        text,
        language: "en",
        style,
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
      audioRef.current.onended = () => setIsPlayingListening(false);
      await audioRef.current.play();
    } catch (error) {
      setIsPlayingListening(false);
      setRunnerError(error instanceof Error ? error.message : "Listening playback failed");
    }
  }

  async function playListeningAudio() {
    if (!listeningTranscript) {
      return;
    }
    await playText(listeningTranscript, "neutral");
  }

  async function startPronunciationRecording(target: string) {
    setRunnerError(null);
    setPronunciationTarget(target);
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
      setIsRecordingPronunciation(true);
    } catch (error) {
      setRunnerError(error instanceof Error ? error.message : "Microphone access failed");
    }
  }

  async function stopPronunciationRecordingAndAssess() {
    const mediaRecorder = mediaRecorderRef.current;
    if (!mediaRecorder || !pronunciationTarget) {
      return;
    }

    setIsAssessingPronunciation(true);
    const recordedBlob = await new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        resolve(new Blob(recordedChunksRef.current, { type: mediaRecorder.mimeType || "audio/webm" }));
      };
      mediaRecorder.stop();
    });
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecordingPronunciation(false);

    try {
      const assessment = await apiClient.assessPronunciation({
        targetText: pronunciationTarget,
        audio: recordedBlob,
      });
      setBlockResponse(activeBlockCurrent.id, assessment.transcript);
      setBlockScore(activeBlockCurrent.id, assessment.score);
    } catch (error) {
      setRunnerError(error instanceof Error ? error.message : "Pronunciation scoring failed");
    } finally {
      setIsAssessingPronunciation(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Lesson Runner")}
        title={tr(lesson.title)}
        description={`${tr(lesson.goal)} ${tr("Duration")}: ${lesson.duration} min. ${tr("Lesson engine already works through config-driven blocks.")}`}
      />

      {lesson.lessonType === "diagnostic" ? (
        <Card className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {tr("Checkpoint mode active. This run is intended to refresh your long-term roadmap across grammar, speaking, listening, pronunciation and writing.")}
        </Card>
      ) : null}

      {runnerError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {runnerError}
        </div>
      ) : null}

      <Card className="space-y-4">
        <LessonStepper blocks={lesson.blocks} activeIndex={selectedBlockIndex} />
      </Card>

      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
              {tt(activeBlockCurrent.blockType)}
            </div>
            <div className="mt-2 text-2xl font-semibold text-ink">{tr(activeBlockCurrent.title)}</div>
          </div>
          <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-700">
            {activeBlockCurrent.estimatedMinutes} min
          </div>
        </div>

        <div className="rounded-2xl bg-sand/80 p-4 text-sm leading-6 text-slate-700">
          {tr(activeBlockCurrent.instructions)}
        </div>

        <div className="grid gap-3">{renderPayload(activeBlockCurrent)}</div>

      {activeBlockCurrent.blockType === "listening_block" && listeningTranscript ? (
          <div className="space-y-3 rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Listening audio")}</div>
            {listeningVariants.length > 1 ? (
              <div className="rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">
                {tr("Active variant")}:{" "}
                <span className="font-semibold text-ink">
                  {selectedListeningVariant?.label ?? `${tr("Variant")} ${selectedListeningVariantIndex + 1}`}
                </span>{" "}
                ({selectedListeningVariantIndex + 1}/{listeningVariants.length})
              </div>
            ) : null}
            {listeningQuestions.length > 0 ? (
              <div className="rounded-2xl bg-sand/80 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">{tr("Questions")}</div>
                <ul className="mt-3 space-y-2 text-sm text-slate-700">
                  {listeningQuestions.map((question) => (
                    <li key={question}>• {question}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div className="flex flex-wrap gap-3">
                  <Button variant="secondary" onClick={() => void playListeningAudio()}>
                    {isPlayingListening ? tr("Playing...") : tr("Play audio prompt")}
              </Button>
              {listeningVariants.length > 1 ? (
                <Button
                  variant="secondary"
                  onClick={() =>
                    setSelectedListeningVariantIndex((currentIndex) => (currentIndex + 1) % listeningVariants.length)
                  }
                >
                  {tr("Switch audio variant")}
                </Button>
              ) : null}
              <Button
                variant="ghost"
                onClick={() =>
                  setShowListeningTranscript((value) => {
                    const nextValue = !value;
                    if (nextValue) {
                      markListeningTranscriptRevealed(activeBlockCurrent.id);
                    }
                    return nextValue;
                  })
                }
              >
                {showListeningTranscript ? tr("Hide transcript") : tr("Reveal transcript")}
              </Button>
            </div>
            {showListeningTranscript ? (
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{listeningTranscript}</div>
            ) : (
              <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                {tr("Try answering from audio first, then reveal transcript only if needed.")}
              </div>
            )}
            {transcriptWasRevealed ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                {tr("Transcript support was used for this checkpoint. Listening score will stay slightly more conservative.")}
              </div>
            ) : null}
          </div>
        ) : null}

        {activeBlockCurrent.blockType === "pronunciation_block" && pronunciationTargets.length > 0 ? (
          <div className="space-y-3 rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Pronunciation checkpoint")}</div>
            {pronunciationTargets.map((target) => (
              <div key={target} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-sand/80 p-3">
                <span className="text-sm text-slate-700">{target}</span>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => void playText(target, "coach")}>
                    {tr("Play model")}
                  </Button>
                  <Button
                    onClick={() =>
                      void (isRecordingPronunciation && pronunciationTarget === target
                        ? stopPronunciationRecordingAndAssess()
                        : startPronunciationRecording(target))
                    }
                    disabled={isAssessingPronunciation}
                  >
                    {isRecordingPronunciation && pronunciationTarget === target
                      ? tr("Stop & score")
                      : isAssessingPronunciation && pronunciationTarget === target
                        ? tr("Scoring...")
                        : tr("Record response")}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <div className="space-y-2">
          <div className="text-sm font-semibold text-ink">{tr("Your response")}</div>
          <textarea
            value={blockResponses[activeBlockCurrent.id] ?? ""}
            onChange={(event) => setBlockResponse(activeBlockCurrent.id, event.target.value)}
            placeholder={tr("Напиши или вставь свой ответ по этому блоку. Он сохранится в lesson run и может попасть в mistakes analytics.")}
            className="min-h-[140px] w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm text-slate-700 outline-none"
          />
        </div>

        {lesson.completed ? (
          <div className="rounded-2xl bg-accent px-4 py-4 text-white">
            {tr("Lesson complete. Estimated score")}: {lesson.score ?? 78}. {tr("Results can now be forwarded into progress and mistakes analytics.")}
          </div>
        ) : (
          <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-600">
            {tr("Draft mode active. Saved block responses will be restored if you leave and reopen this lesson.")}
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <Button variant="ghost" onClick={() => void previousBlock()} disabled={selectedBlockIndex === 0}>
            {tr("Previous")}
          </Button>
          <Button variant="secondary" onClick={() => void saveActiveBlock()}>
            {tr("Save block")}
          </Button>
          <Button variant="secondary" onClick={() => void restartLesson()}>
            {tr("Restart lesson")}
          </Button>
          <Button
            variant="ghost"
            onClick={() => {
              void discardLessonRun();
              navigate(routes.dashboard);
            }}
          >
            {tr("Discard draft")}
          </Button>
          {!isLastBlock ? <Button onClick={() => void nextBlock()}>{tr("Next block")}</Button> : null}
          {isLastBlock ? (
            <Button
              onClick={() => {
                void completeLesson().then(() => navigate(routes.lessonResults));
              }}
            >
              {tr("Complete lesson")}
            </Button>
          ) : null}
        </div>
      </Card>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { LessonBlock } from "../../entities/lesson/model";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { LessonStepper } from "../../shared/ui/LessonStepper";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { getListeningBlockState, getPronunciationTargets } from "./lesson-runner-blocks";
import { LessonBlockPayload } from "./LessonBlockPayload";
import { ListeningBlockPanel } from "./ListeningBlockPanel";
import { PronunciationBlockPanel } from "./PronunciationBlockPanel";
import { useLessonAudio } from "./useLessonAudio";
import { usePronunciationAssessment } from "./usePronunciationAssessment";

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
  const [showListeningTranscript, setShowListeningTranscript] = useState(false);
  const [selectedListeningVariantIndex, setSelectedListeningVariantIndex] = useState(0);
  const [runnerError, setRunnerError] = useState<string | null>(null);

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
  const { listeningVariants, selectedListeningVariant, listeningTranscript, listeningQuestions } =
    getListeningBlockState(activeBlockCurrent, selectedListeningVariantIndex);
  const pronunciationTargets = getPronunciationTargets(activeBlockCurrent);
  const { isPlayingListening, playListeningAudio, playText } = useLessonAudio(setRunnerError);
  const {
    isAssessingPronunciation,
    isRecordingPronunciation,
    pronunciationTarget,
    startPronunciationRecording,
    stopPronunciationRecordingAndAssess,
  } = usePronunciationAssessment({
    onTranscript: (value) => setBlockResponse(activeBlockCurrent.id, value),
    onScore: (value) => setBlockScore(activeBlockCurrent.id, value),
    onError: setRunnerError,
  });

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

        <LessonBlockPayload block={activeBlockCurrent} />

        {activeBlockCurrent.blockType === "listening_block" && listeningTranscript ? (
          <ListeningBlockPanel
            isPlayingListening={isPlayingListening}
            listeningQuestions={listeningQuestions}
            listeningTranscript={listeningTranscript}
            listeningVariants={listeningVariants}
            markTranscriptUsed={() => markListeningTranscriptRevealed(activeBlockCurrent.id)}
            onPlay={() => void playListeningAudio(listeningTranscript)}
            onSwitchVariant={() =>
              setSelectedListeningVariantIndex((currentIndex) => (currentIndex + 1) % listeningVariants.length)
            }
            selectedListeningVariantIndex={selectedListeningVariantIndex}
            selectedListeningVariantLabel={selectedListeningVariant?.label}
            showListeningTranscript={showListeningTranscript}
            toggleTranscript={() => setShowListeningTranscript((value) => !value)}
            transcriptWasRevealed={transcriptWasRevealed}
            tr={tr}
          />
        ) : null}

        {activeBlockCurrent.blockType === "pronunciation_block" && pronunciationTargets.length > 0 ? (
          <PronunciationBlockPanel
            isAssessingPronunciation={isAssessingPronunciation}
            isRecordingPronunciation={isRecordingPronunciation}
            onPlayModel={(target) => void playText(target, "coach")}
            onToggleRecording={(target) =>
              void (isRecordingPronunciation && pronunciationTarget === target
                ? stopPronunciationRecordingAndAssess()
                : startPronunciationRecording(target))
            }
            pronunciationTarget={pronunciationTarget}
            pronunciationTargets={pronunciationTargets}
            tr={tr}
          />
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

import { useLocale } from "../../shared/i18n/useLocale";
import { Card } from "../../shared/ui/Card";
import { LessonStepper } from "../../shared/ui/LessonStepper";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LessonBlockPayload } from "./LessonBlockPayload";
import { LessonRunnerActionBar } from "./LessonRunnerActionBar";
import { LessonRunnerEmptyState } from "./LessonRunnerEmptyState";
import { LessonRunnerResponseField } from "./LessonRunnerResponseField";
import { LessonRunnerStatusBanner } from "./LessonRunnerStatusBanner";
import { ListeningBlockPanel } from "./ListeningBlockPanel";
import { PronunciationBlockPanel } from "./PronunciationBlockPanel";
import { useLessonRunner } from "./useLessonRunner";

export function LessonRunnerScreen() {
  const { tr, tt } = useLocale();
  const {
    activeBlock,
    completeCurrentLesson,
    discardDraft,
    isAssessingPronunciation,
    isLastBlock,
    isPlayingListening,
    isRecordingPronunciation,
    lesson,
    listeningQuestions,
    listeningTranscript,
    listeningVariants,
    nextBlock,
    playListeningPrompt,
    playPronunciationModel,
    previousBlock,
    pronunciationTarget,
    pronunciationTargets,
    responseValue,
    restartLesson,
    runnerError,
    saveActiveBlock,
    selectedBlockIndex,
    selectedListeningVariantIndex,
    selectedListeningVariantLabel,
    showListeningTranscript,
    startLesson,
    switchListeningVariant,
    toggleListeningTranscript,
    togglePronunciationRecording,
    transcriptWasRevealed,
    updateResponse,
  } = useLessonRunner();

  if (!lesson || !activeBlock) {
    return <LessonRunnerEmptyState onBuildLesson={startLesson} tr={tr} />;
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
              {tt(activeBlock.blockType)}
            </div>
            <div className="mt-2 text-2xl font-semibold text-ink">{tr(activeBlock.title)}</div>
          </div>
          <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-700">
            {activeBlock.estimatedMinutes} min
          </div>
        </div>

        <div className="rounded-2xl bg-sand/80 p-4 text-sm leading-6 text-slate-700">
          {tr(activeBlock.instructions)}
        </div>

        <LessonBlockPayload block={activeBlock} />

        {activeBlock.blockType === "listening_block" && listeningTranscript ? (
          <ListeningBlockPanel
            isPlayingListening={isPlayingListening}
            listeningQuestions={listeningQuestions}
            listeningTranscript={listeningTranscript}
            listeningVariants={listeningVariants}
            onPlay={() => void playListeningPrompt()}
            onSwitchVariant={switchListeningVariant}
            selectedListeningVariantIndex={selectedListeningVariantIndex}
            selectedListeningVariantLabel={selectedListeningVariantLabel}
            showListeningTranscript={showListeningTranscript}
            toggleTranscript={toggleListeningTranscript}
            transcriptWasRevealed={transcriptWasRevealed}
            tr={tr}
          />
        ) : null}

        {activeBlock.blockType === "pronunciation_block" && pronunciationTargets.length > 0 ? (
          <PronunciationBlockPanel
            isAssessingPronunciation={isAssessingPronunciation}
            isRecordingPronunciation={isRecordingPronunciation}
            onPlayModel={(target) => void playPronunciationModel(target)}
            onToggleRecording={(target) => void togglePronunciationRecording(target)}
            pronunciationTarget={pronunciationTarget}
            pronunciationTargets={pronunciationTargets}
            tr={tr}
          />
        ) : null}

        <LessonRunnerResponseField onChange={updateResponse} tr={tr} value={responseValue} />

        <LessonRunnerStatusBanner completed={lesson.completed} score={lesson.score} tr={tr} />

        <LessonRunnerActionBar
          canGoBack={selectedBlockIndex > 0}
          isLastBlock={isLastBlock}
          onComplete={completeCurrentLesson}
          onDiscard={discardDraft}
          onNext={nextBlock}
          onPrevious={previousBlock}
          onRestart={restartLesson}
          onSave={saveActiveBlock}
          tr={tr}
        />
      </Card>
    </div>
  );
}

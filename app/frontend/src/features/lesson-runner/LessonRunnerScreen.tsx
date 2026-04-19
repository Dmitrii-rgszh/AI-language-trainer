import { useLocation } from "react-router-dom";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { LessonStepper } from "../../shared/ui/LessonStepper";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LessonBlockPayload } from "./LessonBlockPayload";
import { LessonRunnerActionBar } from "./LessonRunnerActionBar";
import { LessonRunnerEmptyState } from "./LessonRunnerEmptyState";
import { ReadingBlockPanel } from "./ReadingBlockPanel";
import { LessonRunnerResponseField } from "./LessonRunnerResponseField";
import { LessonRunnerStatusBanner } from "./LessonRunnerStatusBanner";
import { ListeningBlockPanel } from "./ListeningBlockPanel";
import { PronunciationBlockPanel } from "./PronunciationBlockPanel";
import { useLessonRunner } from "./useLessonRunner";

export function LessonRunnerScreen() {
  const { tr, tt } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const location = useLocation();
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
    readingPassage,
    readingQuestions,
    readingTitle,
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
  const locationState = (location.state ?? null) as {
    routeEntryReason?: string;
    routeEntrySource?: string;
    routeEntryFollowUpLabel?: string;
    routeEntryStageLabel?: string;
  } | null;
  const showRouteLaunchBridge =
    locationState?.routeEntrySource === "dashboard_route_launch" ||
    locationState?.routeEntrySource === "onboarding_completion";
  const completionBridgeHint =
    dashboard?.journeyState?.nextBestAction ??
    dashboard?.journeyState?.strategySnapshot.routeFollowUpMemory?.followUpLabel ??
    null;
  const ritual = dashboard?.dailyLoopPlan?.ritual ?? null;
  const activeRitualStage =
    ritual?.stages.find((stage) => stage.id === activeBlock?.id) ??
    ritual?.stages[selectedBlockIndex] ??
    null;

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

      {showRouteLaunchBridge && locationState?.routeEntryReason ? (
        <Card className="space-y-4 border border-accent/15 bg-accent/6">
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("Route launch")}</div>
          <div className="text-lg font-semibold text-ink">
            {tr("This lesson is already part of your connected route")}
          </div>
          <div className="rounded-2xl bg-white/80 p-4 text-sm leading-6 text-slate-700">
            {locationState.routeEntryReason}
          </div>
          {locationState.routeEntryFollowUpLabel || locationState.routeEntryStageLabel ? (
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-accent">
                {tr("Now")}: {tr("guided lesson")}
              </span>
              {locationState.routeEntryFollowUpLabel ? (
                <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-coral">
                  {tr("Then")}: {locationState.routeEntryFollowUpLabel}
                </span>
              ) : null}
              {locationState.routeEntryStageLabel ? (
                <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-slate-600">
                  {locationState.routeEntryStageLabel}
                </span>
              ) : null}
            </div>
          ) : null}
        </Card>
      ) : null}

      {ritual ? (
        <Card className="space-y-4 border border-coral/15 bg-white/78">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("Daily ritual")}</div>
              <div className="mt-2 text-lg font-semibold text-ink">{ritual.headline}</div>
              <div className="mt-2 text-sm leading-6 text-slate-700">{ritual.promise}</div>
            </div>
            <div className="rounded-full bg-coral/10 px-3 py-1 text-xs font-semibold text-coral">
              {activeRitualStage ? `${tr("Now")}: ${activeRitualStage.title}` : tr("Connected route")}
            </div>
          </div>
          {activeRitualStage ? (
            <div className="rounded-2xl bg-coral/6 p-4 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">{tr("Current ritual pass")}:</span> {activeRitualStage.summary}
            </div>
          ) : null}
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-2xl bg-white/82 p-4 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">{tr("Completion rule")}:</span> {ritual.completionRule}
            </div>
            <div className="rounded-2xl bg-white/82 p-4 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">{tr("Closure rule")}:</span> {ritual.closureRule}
            </div>
          </div>
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

        {activeBlock.blockType === "reading_block" && readingPassage ? (
          <ReadingBlockPanel
            readingPassage={readingPassage}
            readingQuestions={readingQuestions}
            readingTitle={readingTitle}
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

        {isLastBlock ? (
          <div className="rounded-2xl border border-accent/15 bg-accent/6 p-4 text-sm leading-6 text-slate-700">
            <span className="font-semibold text-ink">{tr("After this block")}:</span>{" "}
            {completionBridgeHint
              ? tr(`Liza will first unpack the session shift in results, then move the route forward through ${completionBridgeHint}.`)
              : tr("Liza will first unpack the session shift in results, then move the route into the updated next step.")}
            {ritual ? ` ${tr("The ritual closes only after the results screen turns this session into the next route step.")}` : ""}
          </div>
        ) : null}

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

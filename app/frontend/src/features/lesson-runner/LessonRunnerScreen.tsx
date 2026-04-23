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
import type { LessonBlock } from "../../entities/lesson/model";
import { Button } from "../../shared/ui/Button";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";

function getPayloadString(block: LessonBlock, keys: string[]) {
  for (const key of keys) {
    const value = block.payload[key];
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    if (Array.isArray(value)) {
      const firstString = value.find((item): item is string => typeof item === "string" && item.trim().length > 0);
      if (firstString) {
        return firstString;
      }
    }
  }

  return null;
}

function getSimpleBlockInstruction(block: LessonBlock, tr: (value: string) => string) {
  switch (block.blockType) {
    case "review_block":
    case "vocab_block":
      return tr("Listen and repeat the phrase.");
    case "speaking_block":
      return tr("Read the prompt and answer shortly.");
    case "grammar_block":
      return tr("Read the phrase and answer shortly.");
    case "listening_block":
      return tr("Listen once, then answer.");
    case "reading_block":
      return tr("Read the short text, then answer.");
    case "pronunciation_block":
      return tr("Listen and repeat slowly.");
    case "writing_block":
      return tr("Write a short answer.");
    case "summary_block":
    case "reflection_block":
      return tr("Finish with one short note.");
    default:
      return tr("Do this step and continue.");
  }
}

function getPrimaryTaskLine(block: LessonBlock) {
  switch (block.blockType) {
    case "review_block":
    case "vocab_block":
      return getPayloadString(block, ["reviewItems", "review_items", "items", "phrases"]);
    case "grammar_block":
    case "speaking_block":
    case "writing_block":
    case "profession_block":
      return getPayloadString(block, ["prompts", "phrases", "brief", "scenario", "targetTerms"]);
    case "summary_block":
    case "reflection_block":
      return getPayloadString(block, ["recapPrompts", "nextStep"]);
    case "pronunciation_block":
      return getPayloadString(block, ["phraseDrills", "phrase_drills", "phrases"]);
    case "reading_block":
      return getPayloadString(block, ["passageTitle", "passage_title", "questions"]);
    case "listening_block":
      return getPayloadString(block, ["questions", "transcript"]);
    default:
      return null;
  }
}

function getResponseFieldCopy(block: LessonBlock, tr: (value: string) => string) {
  switch (block.blockType) {
    case "review_block":
    case "vocab_block":
      return {
        label: tr("Type the translation:"),
        multiline: false,
        placeholder: tr("Write the translation"),
      };
    case "summary_block":
    case "reflection_block":
      return {
        label: tr("Write one short note:"),
        multiline: true,
        placeholder: tr("Write one short note"),
      };
    default:
      return {
        label: tr("Write a short answer:"),
        multiline: true,
        placeholder: tr("Write a short answer"),
      };
  }
}

export function LessonRunnerScreen() {
  const { locale, tr } = useLocale();
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
    playTaskPrompt,
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
    routeEntryCarryLabel?: string;
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

  const progressValue = ((selectedBlockIndex + 1) / lesson.blocks.length) * 100;
  const primaryTaskLine = getPrimaryTaskLine(activeBlock);
  const responseFieldCopy = getResponseFieldCopy(activeBlock, tr);
  const shouldShowResponseField = activeBlock.blockType !== "pronunciation_block";
  const coachMessage =
    locale === "ru"
      ? `Ты продолжаешь урок. Сначала послушай фразу, потом сделай этот шаг.`
      : "You are continuing the lesson. Listen first, then do this step.";
  const coachSpokenMessage =
    locale === "ru"
      ? "Ты продолжаешь урок. Сначала послушай фразу, потом сделай этот шаг."
      : primaryTaskLine
        ? `You are continuing the lesson. First listen to the phrase: ${primaryTaskLine}`
        : "You are continuing the lesson. First listen to the phrase, then do this step.";
  const coachSupportingText =
    locale === "ru"
      ? "Здесь один следующий шаг: услышать образец, понять его и ответить."
      : "There is only one next action here: hear the model, understand it, and answer.";

  return (
    <div className="space-y-4">
      <LizaCoachPanel
        locale={locale}
        playKey={`lesson-runner:${lesson.id}:${activeBlock.id}:${selectedBlockIndex}`}
        message={coachMessage}
        spokenMessage={coachSpokenMessage}
        spokenLanguage={locale}
        replayCta={tr("Hear it again")}
        supportingText={coachSupportingText}
      />

      <Card className="space-y-3 border border-accent/12 bg-white/72">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-coral">{tr("Continue lesson")}</div>
        <div className="text-2xl font-semibold text-ink">{tr("Continue from here")}</div>
        <div className="text-sm text-slate-600">
          {tr("Now")}: <span className="font-semibold text-ink">{tr(activeBlock.title)}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-white/70">
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: `${progressValue}%` }}
          />
        </div>
        <div className="text-sm font-semibold text-slate-600">
          {tr("Step")} {selectedBlockIndex + 1} {tr("of")} {lesson.blocks.length}
        </div>
      </Card>

      {runnerError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {runnerError}
        </div>
      ) : null}

      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="mt-2 text-2xl font-semibold text-ink">{tr(activeBlock.title)}</div>
            <div className="mt-2 text-sm leading-6 text-slate-600">{getSimpleBlockInstruction(activeBlock, tr)}</div>
          </div>
          <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-700">
            {tr("About")} {activeBlock.estimatedMinutes} {tr("min")}
          </div>
        </div>

        {primaryTaskLine ? (
          <div className="rounded-[24px] bg-sand/72 p-4">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{tr("Phrase")}</div>
            <div className="mt-2 text-xl font-semibold leading-8 text-ink">{primaryTaskLine}</div>
            {activeBlock.blockType !== "reading_block" ? (
              <div className="mt-4">
                <Button variant="secondary" onClick={() => void playTaskPrompt(primaryTaskLine, "en")}>
                  {tr("Listen")}
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}

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

        {shouldShowResponseField ? (
          <LessonRunnerResponseField
            compact
            label={responseFieldCopy.label}
            multiline={responseFieldCopy.multiline}
            onChange={updateResponse}
            placeholder={responseFieldCopy.placeholder}
            tr={tr}
            value={responseValue}
          />
        ) : null}

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

      <Card className="space-y-4 border-white/50 bg-white/42 shadow-none opacity-65">
        <LessonStepper blocks={lesson.blocks} activeIndex={selectedBlockIndex} />
      </Card>

      <details className="rounded-[28px] border border-white/50 bg-white/42 p-4 shadow-none">
        <summary className="cursor-pointer text-sm font-semibold text-slate-600 transition-colors hover:text-ink">
          {tr("How this lesson is built")}
        </summary>
        <div className="mt-4 space-y-4">
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
              {locationState.routeEntryFollowUpLabel || locationState.routeEntryCarryLabel || locationState.routeEntryStageLabel ? (
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-accent">
                    {tr("Now")}: {tr("guided lesson")}
                  </span>
                  {locationState.routeEntryFollowUpLabel ? (
                    <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-coral">
                      {tr("Then")}: {tr(locationState.routeEntryFollowUpLabel)}
                    </span>
                  ) : null}
                  {locationState.routeEntryCarryLabel &&
                  locationState.routeEntryCarryLabel !== locationState.routeEntryFollowUpLabel ? (
                    <span className="rounded-full bg-sand px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-ink">
                      {tr("Carry")}: {tr(locationState.routeEntryCarryLabel ?? "")}
                    </span>
                  ) : null}
                  {locationState.routeEntryStageLabel ? (
                    <span className="rounded-full bg-white/82 px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.14em] text-slate-600">
                      {tr(locationState.routeEntryStageLabel)}
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

          {isLastBlock ? (
            <Card className="space-y-3 border border-accent/15 bg-accent/6">
              <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("After this block")}</div>
              <div className="text-sm leading-6 text-slate-700">
                {completionBridgeHint
                  ? `${tr("Liza will first show the session result, then move the route forward through")} ${tr(completionBridgeHint)}.`
                  : tr("Liza will first show the session result, then move the route to the next step.")}
                {ritual ? ` ${tr("The ritual closes only after the results screen turns this session into the next route step.")}` : ""}
              </div>
            </Card>
          ) : null}

          <Card className="space-y-4">
            <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">{tr("Full step plan")}</div>
            <div className="rounded-2xl bg-sand/80 p-4 text-sm leading-6 text-slate-700">
              {tr(activeBlock.instructions)}
            </div>
            <LessonBlockPayload block={activeBlock} mode="all" tr={tr} />
          </Card>
        </div>
      </details>
    </div>
  );
}

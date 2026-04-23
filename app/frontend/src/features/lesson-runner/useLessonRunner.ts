import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useAppStore } from "../../shared/store/app-store";
import { getListeningBlockState, getPronunciationTargets, getReadingBlockState } from "./lesson-runner-blocks";
import { useLessonAudio } from "./useLessonAudio";
import { usePronunciationAssessment } from "./usePronunciationAssessment";

export function useLessonRunner() {
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
  const activeBlock = lesson?.blocks[selectedBlockIndex] ?? lesson?.blocks[0] ?? null;
  const activeBlockId = activeBlock?.id ?? null;
  const transcriptWasRevealed = activeBlockId ? (listeningTranscriptReveals[activeBlockId] ?? false) : false;
  const { isPlayingListening, playListeningAudio, playText } = useLessonAudio(setRunnerError);
  const {
    isAssessingPronunciation,
    isRecordingPronunciation,
    pronunciationTarget,
    startPronunciationRecording,
    stopPronunciationRecordingAndAssess,
  } = usePronunciationAssessment({
    onTranscript: (blockId, value) => setBlockResponse(blockId, value),
    onScore: (blockId, value) => setBlockScore(blockId, value),
    onError: setRunnerError,
  });

  useEffect(() => {
    if (!lesson) {
      void resumeLessonRun();
    }
  }, [lesson, resumeLessonRun]);

  useEffect(() => {
    setShowListeningTranscript(transcriptWasRevealed);
    setSelectedListeningVariantIndex(0);
  }, [activeBlockId, transcriptWasRevealed]);

  const listeningState = activeBlock
    ? getListeningBlockState(activeBlock, selectedListeningVariantIndex)
    : {
        listeningQuestions: [],
        listeningTranscript: null,
        listeningVariants: [],
        selectedListeningVariant: null,
      };
  const readingState = activeBlock
    ? getReadingBlockState(activeBlock)
    : {
        readingPassage: null,
        readingQuestions: [],
        readingTitle: null,
      };
  const pronunciationTargets = activeBlock ? getPronunciationTargets(activeBlock) : [];
  const responseValue = activeBlockId ? (blockResponses[activeBlockId] ?? "") : "";
  const isLastBlock = lesson ? selectedBlockIndex === lesson.blocks.length - 1 : false;

  function updateResponse(value: string) {
    if (!activeBlockId) {
      return;
    }

    setBlockResponse(activeBlockId, value);
  }

  function toggleListeningTranscript() {
    if (!showListeningTranscript && activeBlockId) {
      markListeningTranscriptRevealed(activeBlockId);
    }

    setShowListeningTranscript((value) => !value);
  }

  function switchListeningVariant() {
    if (listeningState.listeningVariants.length <= 1) {
      return;
    }

    setSelectedListeningVariantIndex(
      (currentIndex) => (currentIndex + 1) % listeningState.listeningVariants.length,
    );
  }

  async function playListeningPrompt() {
    await playListeningAudio(listeningState.listeningTranscript);
  }

  async function playPronunciationModel(target: string) {
    await playText(target, {
      language: "en",
      style: "neutral",
      speaker: "Ana Florence",
    });
  }

  async function playTaskPrompt(text: string, language: "ru" | "en" = "en") {
    await playText(text, {
      language,
      style: language === "en" ? "neutral" : "coach",
      speaker: language === "en" ? "Ana Florence" : null,
    });
  }

  async function togglePronunciationRecording(target: string) {
    if (!activeBlockId) {
      return;
    }

    if (isRecordingPronunciation && pronunciationTarget === target) {
      await stopPronunciationRecordingAndAssess();
      return;
    }

    await startPronunciationRecording(target, activeBlockId);
  }

  async function discardDraft() {
    await discardLessonRun();
    const updatedDashboard = useAppStore.getState().dashboard;
    navigate(routes.dashboard, {
      state: {
        routeEntryReason:
          updatedDashboard?.journeyState?.currentFocusArea
            ? `The draft was closed, but the route itself is still alive around ${updatedDashboard.journeyState.currentFocusArea}. The dashboard is opening so you can re-enter through the strongest next step instead of starting from scratch.`
            : "The draft was closed, but the route itself is still alive. The dashboard is opening so you can re-enter through the strongest next step instead of starting from scratch.",
        routeEntrySource: "lesson_discard",
        routeEntryFollowUpLabel:
          updatedDashboard?.journeyState?.nextBestAction ??
          updatedDashboard?.dailyLoopPlan?.nextStepHint ??
          "updated route",
        routeEntryCarryLabel:
          updatedDashboard?.journeyState?.strategySnapshot.routeFollowUpMemory?.carryLabel ?? null,
        routeEntryStageLabel: "Route preserved",
      },
    });
  }

  async function completeCurrentLesson() {
    await completeLesson();
    const updatedDashboard = useAppStore.getState().dashboard;
    const nextBestAction =
      updatedDashboard?.journeyState?.nextBestAction ??
      updatedDashboard?.dailyLoopPlan?.nextStepHint ??
      "updated dashboard";
    navigate(routes.lessonResults, {
      state: {
        routeEntryReason:
          updatedDashboard?.journeyState?.currentFocusArea
            ? `The route has already been recalculated around ${updatedDashboard.journeyState.currentFocusArea}, so results open first to explain the shift before the next step starts.`
            : "The route has already been recalculated, so results open first to explain the shift before the next step starts.",
        routeEntrySource: "lesson_completion",
        routeEntryFollowUpLabel: nextBestAction,
        routeEntryCarryLabel:
          updatedDashboard?.journeyState?.strategySnapshot.routeFollowUpMemory?.carryLabel ?? null,
        routeEntryStageLabel: "Route updated",
      },
    });
  }

  return {
    activeBlock,
    completeCurrentLesson,
    discardDraft,
    isAssessingPronunciation,
    isLastBlock,
    isPlayingListening,
    isRecordingPronunciation,
    lesson,
    listeningQuestions: listeningState.listeningQuestions,
    listeningTranscript: listeningState.listeningTranscript,
    listeningVariants: listeningState.listeningVariants,
    readingPassage: readingState.readingPassage,
    readingQuestions: readingState.readingQuestions,
    readingTitle: readingState.readingTitle,
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
    selectedListeningVariantLabel: listeningState.selectedListeningVariant?.label,
    showListeningTranscript,
    startLesson,
    switchListeningVariant,
    toggleListeningTranscript,
    togglePronunciationRecording,
    transcriptWasRevealed,
    updateResponse,
  };
}

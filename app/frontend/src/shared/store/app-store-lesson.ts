import type { BlockResultSubmission, Lesson, LessonResultSummary } from "../../entities/lesson/model";
import { apiClient } from "../api/client";
import { buildBlockScore } from "../lib/lesson-run-scoring";
import { hydrateLessonRunState } from "../lib/lesson-run-state";
import { createEmptyLessonRunState } from "./app-store.state";
import type { AppState, AppStoreGet, AppStoreSet } from "./app-store.types";

type LessonActionKeys =
  | "startLesson"
  | "startDiagnosticCheckpoint"
  | "startRecoveryLesson"
  | "resumeLessonRun"
  | "discardLessonRun"
  | "restartLesson"
  | "setBlockResponse"
  | "setBlockScore"
  | "markListeningTranscriptRevealed"
  | "saveActiveBlock"
  | "nextBlock"
  | "previousBlock"
  | "completeLesson";

function buildBlockResultSubmission(params: {
  block: Lesson["blocks"][number];
  blockIndex: number;
  explicitScore?: number;
  lesson: Lesson;
  responseText: string;
  transcriptRevealed: boolean;
}): BlockResultSubmission {
  const { block, blockIndex, explicitScore, lesson, responseText, transcriptRevealed } = params;
  const score = buildBlockScore({
    lessonType: lesson.lessonType,
    block,
    responseText,
    explicitScore,
    transcriptRevealed,
  });

  return {
    blockId: block.id,
    userResponseType: responseText.trim() ? "text" : "none",
    userResponse: responseText,
    feedbackSummary:
      block.blockType === "listening_block" && transcriptRevealed
        ? `Block ${blockIndex + 1} completed in lesson runner. Transcript support was used for this listening block.`
        : `Block ${blockIndex + 1} completed in lesson runner.`,
    score,
  };
}

function buildActiveBlockSubmission(state: AppState): BlockResultSubmission | null {
  if (!state.lesson) {
    return null;
  }

  const activeBlock = state.lesson.blocks[state.selectedBlockIndex];
  if (!activeBlock) {
    return null;
  }

  const responseText = state.blockResponses[activeBlock.id] ?? "";
  const transcriptRevealed = state.listeningTranscriptReveals[activeBlock.id] ?? false;
  const submission = buildBlockResultSubmission({
    lesson: state.lesson,
    block: activeBlock,
    blockIndex: state.selectedBlockIndex,
    responseText,
    explicitScore: state.blockScores[activeBlock.id],
    transcriptRevealed,
  });

  return {
    ...submission,
    feedbackSummary:
      activeBlock.blockType === "listening_block" && transcriptRevealed
        ? `Saved from lesson runner at step ${state.selectedBlockIndex + 1}. Transcript support was used for this listening block.`
        : `Saved from lesson runner at step ${state.selectedBlockIndex + 1}.`,
  };
}

function buildCompletionResults(state: AppState): BlockResultSubmission[] {
  if (!state.lesson) {
    return [];
  }

  return state.lesson.blocks.map((block, index) =>
    buildBlockResultSubmission({
      lesson: state.lesson as Lesson,
      block,
      blockIndex: index,
      responseText: state.blockResponses[block.id] ?? "",
      explicitScore: state.blockScores[block.id],
      transcriptRevealed: state.listeningTranscriptReveals[block.id] ?? false,
    }),
  );
}

function buildCheckpointSkillInsights(
  lesson: Lesson,
  blockResults: BlockResultSubmission[],
  transcriptReveals: Record<string, boolean>,
): LessonResultSummary["checkpointSkillInsights"] {
  if (lesson.lessonType !== "diagnostic") {
    return undefined;
  }

  return lesson.blocks
    .map((block) => {
      const blockResult = blockResults.find((item) => item.blockId === block.id);
      if (!blockResult?.score) {
        return null;
      }

      if (block.blockType === "listening_block") {
        return {
          skill: "Listening",
          checkpointScore: blockResult.score,
          note: transcriptReveals[block.id]
            ? "Transcript was revealed during the checkpoint, so listening readiness was scored with extra caution."
            : "Audio-first answer held up without transcript help, which supports stronger listening readiness.",
        };
      }

      if (block.blockType === "pronunciation_block") {
        const soundFocus = Array.isArray(block.payload.sound_focus)
          ? block.payload.sound_focus.filter((item): item is string => typeof item === "string")
          : [];

        return {
          skill: "Pronunciation",
          checkpointScore: blockResult.score,
          note:
            blockResult.score >= 75
              ? `Pronunciation scoring held up well${soundFocus.length > 0 ? ` on ${soundFocus.join(", ")}` : ""}, which helped push voice readiness upward.`
              : `Pronunciation scoring stayed cautious${soundFocus.length > 0 ? ` around ${soundFocus.join(", ")}` : ""}, so roadmap readiness did not rise as fast here.`,
        };
      }

      return null;
    })
    .filter((item): item is NonNullable<typeof item> => item !== null);
}

function buildLessonResultSummary(params: {
  blockResults: BlockResultSubmission[];
  completedAt?: string;
  completedBlocks: number;
  dashboard: AppState["dashboard"];
  diagnosticRoadmap: AppState["diagnosticRoadmap"];
  lesson: Lesson;
  mistakes: AppState["mistakes"];
  previousProgress: AppState["progress"];
  previousRoadmap: AppState["diagnosticRoadmap"];
  progress: NonNullable<AppState["progress"]>;
  runId: string;
  score: number;
  transcriptReveals: Record<string, boolean>;
}): LessonResultSummary {
  const {
    blockResults,
    completedAt,
    completedBlocks,
    dashboard,
    diagnosticRoadmap,
    lesson,
    mistakes,
    previousProgress,
    previousRoadmap,
    progress,
    runId,
    score,
    transcriptReveals,
  } = params;

  return {
    runId,
    title: lesson.title,
    score,
    completedAt,
    completedBlocks,
    totalBlocks: lesson.blocks.length,
    mistakes,
    progressBefore: previousProgress,
    progressAfter: progress,
    nextRecommendationTitle: dashboard?.recommendation.title,
    nextRecommendationGoal: dashboard?.recommendation.goal,
    diagnosticEstimatedLevelBefore: previousRoadmap?.estimatedLevel,
    diagnosticEstimatedLevelAfter: diagnosticRoadmap?.estimatedLevel,
    diagnosticOverallScoreBefore: previousRoadmap?.overallScore,
    diagnosticOverallScoreAfter: diagnosticRoadmap?.overallScore,
    milestoneDeltas:
      previousRoadmap && diagnosticRoadmap
        ? diagnosticRoadmap.milestones.map((milestone) => {
            const previousMilestone = previousRoadmap.milestones.find((item) => item.level === milestone.level);
            return {
              level: milestone.level,
              readinessBefore: previousMilestone?.readiness ?? 0,
              readinessAfter: milestone.readiness,
            };
          })
        : undefined,
    checkpointSkillInsights: buildCheckpointSkillInsights(
      lesson,
      blockResults,
      transcriptReveals,
    ),
  };
}

function buildOverallScore(blockResults: BlockResultSubmission[]) {
  if (blockResults.length === 0) {
    return 78;
  }

  return Math.round(blockResults.reduce((total, block) => total + (block.score ?? 0), 0) / blockResults.length);
}

async function resolveActiveLessonRunId(get: AppStoreGet) {
  return get().activeLessonRunId ?? (await apiClient.getActiveLessonRun())?.runId ?? null;
}

export function createLessonActions(
  set: AppStoreSet,
  get: AppStoreGet,
): Pick<AppState, LessonActionKeys> {
  return {
    startLesson: async () => {
      const activeLessonRun = await apiClient.getActiveLessonRun();
      if (activeLessonRun) {
        set(hydrateLessonRunState(activeLessonRun));
        return;
      }

      const lessonRun = await apiClient.startLessonRun();
      set(hydrateLessonRunState(lessonRun));
    },
    startDiagnosticCheckpoint: async () => {
      const lessonRun = await apiClient.startDiagnosticCheckpoint();
      set(hydrateLessonRunState(lessonRun));
    },
    startRecoveryLesson: async () => {
      const lessonRun = await apiClient.startRecoveryRun();
      set(hydrateLessonRunState(lessonRun));
    },
    resumeLessonRun: async () => {
      const activeLessonRun = await apiClient.getActiveLessonRun();
      if (!activeLessonRun) {
        return false;
      }

      set(hydrateLessonRunState(activeLessonRun));
      return true;
    },
    discardLessonRun: async () => {
      const activeLessonRunId = await resolveActiveLessonRunId(get);
      if (!activeLessonRunId) {
        return;
      }

      await apiClient.discardLessonRun(activeLessonRunId);
      const dashboard = await apiClient.getDashboardData();

      set({
        ...createEmptyLessonRunState(),
        dashboard,
      });
    },
    restartLesson: async () => {
      const activeLessonRunId = await resolveActiveLessonRunId(get);
      const lessonRun = activeLessonRunId
        ? await apiClient.restartLessonRun(activeLessonRunId)
        : await apiClient.startLessonRun();
      const dashboard = await apiClient.getDashboardData();

      set({
        ...hydrateLessonRunState(lessonRun),
        lastLessonResult: null,
        blockScores: {},
        listeningTranscriptReveals: {},
        dashboard,
      });
    },
    setBlockResponse: (blockId, value) => {
      set((state) => ({
        blockResponses: {
          ...state.blockResponses,
          [blockId]: value,
        },
      }));
    },
    setBlockScore: (blockId, score) => {
      set((state) => ({
        blockScores: {
          ...state.blockScores,
          [blockId]: score,
        },
      }));
    },
    markListeningTranscriptRevealed: (blockId) => {
      set((state) => ({
        listeningTranscriptReveals: {
          ...state.listeningTranscriptReveals,
          [blockId]: true,
        },
      }));
    },
    saveActiveBlock: async () => {
      const state = get();
      if (!state.lesson || !state.activeLessonRunId) {
        return;
      }

      const activeBlock = state.lesson.blocks[state.selectedBlockIndex];
      if (!activeBlock) {
        return;
      }

      const submission = buildActiveBlockSubmission(state);
      if (!submission) {
        return;
      }

      const lessonRun = await apiClient.submitBlockResult(state.activeLessonRunId, submission);
      const responseText = state.blockResponses[activeBlock.id] ?? "";

      set((current) => ({
        ...hydrateLessonRunState(lessonRun),
        lastLessonResult: current.lastLessonResult,
        blockResponses: {
          ...current.blockResponses,
          [activeBlock.id]: responseText,
        },
      }));
    },
    nextBlock: async () => {
      const lesson = get().lesson;
      if (!lesson) {
        return;
      }

      await get().saveActiveBlock();
      set((state) => ({
        selectedBlockIndex: Math.min(state.selectedBlockIndex + 1, lesson.blocks.length - 1),
      }));
    },
    previousBlock: async () => {
      await get().saveActiveBlock();
      set((state) => ({
        selectedBlockIndex: Math.max(state.selectedBlockIndex - 1, 0),
      }));
    },
    completeLesson: async () => {
      const state = get();
      if (!state.lesson || !state.activeLessonRunId) {
        return;
      }

      const blockResults = buildCompletionResults(state);
      const overallScore = buildOverallScore(blockResults);
      const response = await apiClient.completeLessonRun(
        state.activeLessonRunId,
        overallScore,
        state.lesson.duration,
        blockResults,
      );

      const [dashboard, mistakes, diagnosticRoadmap] = await Promise.all([
        apiClient.getDashboardData(),
        apiClient.getMistakes(),
        apiClient.getDiagnosticRoadmap(),
      ]);

      const resultSummary = buildLessonResultSummary({
        runId: response.lessonRun.runId,
        lesson: response.lessonRun.lesson,
        blockResults,
        completedAt: response.lessonRun.completedAt,
        completedBlocks: response.lessonRun.blockRuns.filter((blockRun) => blockRun.status === "completed").length,
        dashboard,
        mistakes: response.mistakes,
        progress: response.progress,
        previousProgress: state.progress,
        diagnosticRoadmap,
        previousRoadmap: state.diagnosticRoadmap,
        score: response.lessonRun.score ?? overallScore,
        transcriptReveals: state.listeningTranscriptReveals,
      });

      set({
        ...createEmptyLessonRunState(),
        lesson: { ...response.lessonRun.lesson, completed: true, score: response.lessonRun.score ?? overallScore },
        lastLessonResult: resultSummary,
        progress: response.progress,
        diagnosticRoadmap,
        dashboard,
        mistakes: response.mistakes.length > 0 ? response.mistakes : mistakes,
      });
    },
  };
}

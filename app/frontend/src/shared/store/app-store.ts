import { create } from "zustand";
import type { UserAccount, UserAccountDraft } from "../../entities/account/model";
import type { BlockResultSubmission, Lesson, LessonResultSummary } from "../../entities/lesson/model";
import type { Mistake } from "../../entities/mistake/model";
import type { CompleteOnboardingRequest, UserOnboarding } from "../../entities/onboarding/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import type { UserProfile } from "../../entities/user/model";
import type {
  DashboardData,
  DiagnosticRoadmap,
  GrammarTopic,
  ProfessionTrackCard,
  PronunciationDrill,
  ProviderPreference,
  ProviderStatus,
  SpeakingScenario,
  WritingTask,
} from "../types/app-data";
import { ApiError, apiClient } from "../api/client";
import {
  clearStoredActiveUserId,
  readStoredActiveUserId,
  writeStoredActiveUserId,
} from "../auth/active-user";
import { normalizeLocale, readStoredLocale, type AppLocale, writeStoredLocale } from "../i18n/locale";

function normalizeText(value: string) {
  return value.toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ");
}

function countKeywordMatches(responseText: string, keywords: string[]) {
  const normalizedResponse = normalizeText(responseText);
  return keywords.filter((keyword) => normalizedResponse.includes(normalizeText(keyword))).length;
}

type ListeningQuestionRule = {
  prompt: string;
  acceptableAnswers: string[];
};

function parseListeningQuestionRule(value: unknown): ListeningQuestionRule | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const prompt = "prompt" in value && typeof value.prompt === "string" ? value.prompt : null;
  const acceptableAnswers =
    "acceptable_answers" in value && Array.isArray(value.acceptable_answers)
      ? value.acceptable_answers.filter((item): item is string => typeof item === "string")
      : [];

  if (!prompt || acceptableAnswers.length === 0) {
    return null;
  }

  return { prompt, acceptableAnswers };
}

function extractListeningQuestionSets(block: Lesson["blocks"][number]) {
  const variants = Array.isArray(block.payload.audio_variants) ? block.payload.audio_variants : [];
  const parsedVariants = variants
    .map((variant) => {
      if (!variant || typeof variant !== "object") {
        return null;
      }

      const transcript = "transcript" in variant && typeof variant.transcript === "string" ? variant.transcript : null;
      const label = "label" in variant && typeof variant.label === "string" ? variant.label : "Audio variant";
      const questions =
        "questions" in variant && Array.isArray(variant.questions)
          ? variant.questions
              .map(parseListeningQuestionRule)
              .filter((item: ListeningQuestionRule | null): item is ListeningQuestionRule => item !== null)
          : [];

      if (!transcript || questions.length === 0) {
        return null;
      }

      return {
        label,
        transcript,
        questions,
      };
    })
    .filter(
      (
        item: { label: string; transcript: string; questions: ListeningQuestionRule[] } | null,
      ): item is { label: string; transcript: string; questions: ListeningQuestionRule[] } => item !== null,
    );

  if (parsedVariants.length > 0) {
    return parsedVariants;
  }

  const fallbackQuestions = Array.isArray(block.payload.questions)
    ? block.payload.questions
        .filter((item): item is string => typeof item === "string")
        .map((prompt) => ({ prompt, acceptableAnswers: [] as string[] }))
    : [];
  const fallbackAnswers = Array.isArray(block.payload.answer_key)
    ? block.payload.answer_key.filter((item): item is string => typeof item === "string")
    : Array.isArray(block.payload.answerKey)
      ? block.payload.answerKey.filter((item): item is string => typeof item === "string")
      : [];

  if (fallbackQuestions.length === 0 && fallbackAnswers.length === 0) {
    return [];
  }

  return [
    {
      label: "Primary audio",
      transcript: typeof block.payload.transcript === "string" ? block.payload.transcript : "",
      questions:
        fallbackQuestions.length > 0
          ? fallbackQuestions.map((question, index) => ({
              prompt: question.prompt,
              acceptableAnswers: fallbackAnswers[index] ? [fallbackAnswers[index]] : fallbackAnswers,
            }))
          : [{ prompt: "Listening answer", acceptableAnswers: fallbackAnswers }],
    },
  ];
}

function scoreListeningResponse(
  block: Lesson["blocks"][number],
  responseText: string,
  transcriptRevealed: boolean,
  baseScore: number,
) {
  const variants = extractListeningQuestionSets(block);
  if (variants.length === 0) {
    return Math.max(25, Math.min(95, Math.round(baseScore - (transcriptRevealed ? 12 : 0))));
  }

  const bestCoverage = variants.reduce((best, variant) => {
    const matchedQuestions = variant.questions.filter((question) => {
      if (question.acceptableAnswers.length === 0) {
        return false;
      }
      return countKeywordMatches(responseText, question.acceptableAnswers) > 0;
    }).length;
    const coverage = matchedQuestions / variant.questions.length;
    return Math.max(best, coverage);
  }, 0);

  const coverageScore = 42 + bestCoverage * 48;
  const completenessBoost = responseText.trim().length > 0 ? Math.min(8, responseText.trim().split(/\s+/).length) : 0;
  const revealPenalty = transcriptRevealed ? 12 : 0;

  return Math.max(25, Math.min(95, Math.round(Math.max(baseScore - 8, coverageScore + completenessBoost) - revealPenalty)));
}

function buildBlockScore(params: {
  lessonType: Lesson["lessonType"];
  block: Lesson["blocks"][number];
  responseText: string;
  explicitScore?: number;
  transcriptRevealed?: boolean;
}) {
  const { lessonType, block, responseText, explicitScore, transcriptRevealed = false } = params;
  if (typeof explicitScore === "number") {
    return explicitScore;
  }

  const trimmedResponse = responseText.trim();
  const wordCount = trimmedResponse.split(/\s+/).filter(Boolean).length;
  const baseScore = trimmedResponse.length === 0 ? 45 : Math.min(92, 52 + wordCount * 3);

  if (block.blockType === "listening_block") {
    return scoreListeningResponse(block, trimmedResponse, transcriptRevealed, baseScore);
  }

  if (lessonType !== "diagnostic") {
    return Math.max(55, baseScore);
  }
  if (block.blockType === "writing_block") {
    return Math.min(95, baseScore + 3);
  }
  return baseScore;
}

function hydrateLessonRunState(
  lessonRun: {
    runId: string;
    lesson: Lesson;
    blockRuns: Array<{
      blockId: string;
      userResponse?: string;
      transcript?: string;
      status: string;
      score?: number;
    }>;
  },
) {
  const blockResponses = Object.fromEntries(
    lessonRun.blockRuns
      .map((blockRun) => [blockRun.blockId, blockRun.userResponse ?? blockRun.transcript ?? ""])
      .filter((entry) => entry[1].trim().length > 0),
  );
  const blockScores = Object.fromEntries(
    lessonRun.blockRuns
      .filter((blockRun) => typeof blockRun.score === "number")
      .map((blockRun) => [blockRun.blockId, blockRun.score as number]),
  );
  const firstIncompleteIndex = lessonRun.lesson.blocks.findIndex((block) => {
    const blockRun = lessonRun.blockRuns.find((item) => item.blockId === block.id);
    return blockRun?.status !== "completed";
  });

  return {
    lesson: lessonRun.lesson,
    activeLessonRunId: lessonRun.runId,
    selectedBlockIndex: firstIncompleteIndex >= 0 ? firstIncompleteIndex : lessonRun.lesson.blocks.length - 1,
    blockResponses,
    blockScores,
  };
}

interface AppState {
  locale: AppLocale;
  isBootstrapping: boolean;
  bootstrapError: string | null;
  needsOnboarding: boolean;
  currentUser: UserAccount | null;
  currentOnboarding: UserOnboarding | null;
  profile: UserProfile | null;
  dashboard: DashboardData | null;
  lesson: Lesson | null;
  lastLessonResult: LessonResultSummary | null;
  activeLessonRunId: string | null;
  selectedBlockIndex: number;
  blockResponses: Record<string, string>;
  blockScores: Record<string, number>;
  grammarTopics: GrammarTopic[];
  speakingScenarios: SpeakingScenario[];
  pronunciationDrills: PronunciationDrill[];
  writingTask: WritingTask | null;
  professionTracks: ProfessionTrackCard[];
  mistakes: Mistake[];
  progress: ProgressSnapshot | null;
  diagnosticRoadmap: DiagnosticRoadmap | null;
  providers: ProviderStatus[];
  providerPreferences: ProviderPreference[];
  listeningTranscriptReveals: Record<string, boolean>;
  setLocale: (locale: AppLocale) => void;
  bootstrap: () => Promise<void>;
  completeOnboarding: (payload: CompleteOnboardingRequest) => Promise<void>;
  saveCurrentUser: (payload: UserAccountDraft) => Promise<void>;
  saveProfile: (profile: UserProfile) => Promise<void>;
  saveProviderPreference: (providerType: ProviderPreference["providerType"], enabled: boolean) => Promise<void>;
  startLesson: () => Promise<void>;
  startDiagnosticCheckpoint: () => Promise<void>;
  startRecoveryLesson: () => Promise<void>;
  resumeLessonRun: () => Promise<boolean>;
  discardLessonRun: () => Promise<void>;
  restartLesson: () => Promise<void>;
  setBlockResponse: (blockId: string, value: string) => void;
  setBlockScore: (blockId: string, score: number) => void;
  markListeningTranscriptRevealed: (blockId: string) => void;
  saveActiveBlock: () => Promise<void>;
  nextBlock: () => Promise<void>;
  previousBlock: () => Promise<void>;
  completeLesson: () => Promise<void>;
}

export const useAppStore = create<AppState>((set, get) => ({
  locale: readStoredLocale() ?? "ru",
  isBootstrapping: false,
  bootstrapError: null,
  needsOnboarding: false,
  currentUser: null,
  currentOnboarding: null,
  profile: null,
  dashboard: null,
  lesson: null,
  lastLessonResult: null,
  activeLessonRunId: null,
  selectedBlockIndex: 0,
  blockResponses: {},
  blockScores: {},
  grammarTopics: [],
  speakingScenarios: [],
  pronunciationDrills: [],
  writingTask: null,
  professionTracks: [],
  mistakes: [],
  progress: null,
  diagnosticRoadmap: null,
  providers: [],
  providerPreferences: [],
  listeningTranscriptReveals: {},
  setLocale: (locale) => {
    const normalizedLocale = normalizeLocale(locale);
    writeStoredLocale(normalizedLocale);

    set((state) => ({
      locale: normalizedLocale,
      profile: state.profile ? { ...state.profile, preferredUiLanguage: normalizedLocale } : state.profile,
      dashboard: state.dashboard
        ? {
            ...state.dashboard,
            profile: { ...state.dashboard.profile, preferredUiLanguage: normalizedLocale },
          }
        : state.dashboard,
    }));
  },
  bootstrap: async () => {
    if (get().isBootstrapping) {
      return;
    }

    set({ isBootstrapping: true, bootstrapError: null });

    try {
      const [
        grammarTopics,
        speakingScenarios,
        pronunciationDrills,
        writingTask,
        professionTracks,
        providers,
      ] = await Promise.all([
        apiClient.getGrammarTopics(),
        apiClient.getSpeakingScenarios(),
        apiClient.getPronunciationDrills(),
        apiClient.getWritingTask(),
        apiClient.getProfessionTracks(),
        apiClient.getProviders(),
      ]);

      set({
        grammarTopics,
        speakingScenarios,
        pronunciationDrills,
        writingTask,
        professionTracks,
        providers,
      });

      const activeUserId = readStoredActiveUserId();
      if (!activeUserId) {
        set({
          isBootstrapping: false,
          bootstrapError: null,
          needsOnboarding: true,
          currentUser: null,
          currentOnboarding: null,
          profile: null,
          dashboard: null,
          lesson: null,
          lastLessonResult: null,
          activeLessonRunId: null,
          blockResponses: {},
          blockScores: {},
          listeningTranscriptReveals: {},
          mistakes: [],
          progress: null,
          diagnosticRoadmap: null,
          providerPreferences: [],
        });
        return;
      }

      let currentUser: UserAccount;
      try {
        currentUser = await apiClient.getCurrentUser();
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          clearStoredActiveUserId();
          set({
            isBootstrapping: false,
            bootstrapError: null,
            needsOnboarding: true,
            currentUser: null,
            currentOnboarding: null,
            profile: null,
            dashboard: null,
            lesson: null,
            lastLessonResult: null,
            activeLessonRunId: null,
            blockResponses: {},
            blockScores: {},
            listeningTranscriptReveals: {},
            mistakes: [],
            progress: null,
            diagnosticRoadmap: null,
            providerPreferences: [],
          });
          return;
        }

        throw error;
      }

      let currentOnboarding: UserOnboarding | null = null;
      try {
        currentOnboarding = await apiClient.getCurrentOnboarding();
      } catch (error) {
        if (!(error instanceof ApiError && error.status === 404)) {
          throw error;
        }
      }

      let profile: UserProfile;
      try {
        profile = await apiClient.getProfile();
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          set({
            isBootstrapping: false,
            bootstrapError: null,
            needsOnboarding: true,
            currentUser,
            currentOnboarding,
            profile: null,
            dashboard: null,
            lesson: null,
            lastLessonResult: null,
            activeLessonRunId: null,
            blockResponses: {},
            blockScores: {},
            listeningTranscriptReveals: {},
            mistakes: [],
            progress: null,
            diagnosticRoadmap: null,
            providerPreferences: [],
          });
          return;
        }

        throw error;
      }

      const [dashboard, mistakes, progress, diagnosticRoadmap, providerPreferences] = await Promise.all([
        apiClient.getDashboardData(),
        apiClient.getMistakes(),
        apiClient.getProgress(),
        apiClient.getDiagnosticRoadmap(),
        apiClient.getProviderPreferences(),
      ]);

      const storedLocale = readStoredLocale();
      const nextLocale = storedLocale ?? normalizeLocale(profile.preferredUiLanguage, get().locale);

      if (!storedLocale) {
        writeStoredLocale(nextLocale);
      }

      set({
        locale: nextLocale,
        isBootstrapping: false,
        bootstrapError: null,
        needsOnboarding: false,
        currentUser,
        currentOnboarding,
        profile,
        dashboard,
        lesson: null,
        lastLessonResult: null,
        activeLessonRunId: null,
        blockResponses: {},
        blockScores: {},
        listeningTranscriptReveals: {},
        mistakes,
        progress,
        diagnosticRoadmap,
        providerPreferences,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to bootstrap app data";
      set({ isBootstrapping: false, bootstrapError: message });
    }
  },
  completeOnboarding: async (payload) => {
    const response = await apiClient.completeOnboarding(payload);
    writeStoredActiveUserId(response.user.id);
    const nextLocale = normalizeLocale(response.profile.preferredUiLanguage, get().locale);
    writeStoredLocale(nextLocale);
    set({
      locale: nextLocale,
      bootstrapError: null,
      needsOnboarding: false,
      currentUser: response.user,
      currentOnboarding: response.onboarding,
      profile: response.profile,
    });
    await get().bootstrap();
  },
  saveCurrentUser: async (payload) => {
    const savedUser = await apiClient.saveCurrentUser(payload);
    set({ currentUser: savedUser });
  },
  saveProfile: async (profile) => {
    const savedProfile = await apiClient.saveProfile(profile);
    const nextLocale = normalizeLocale(savedProfile.preferredUiLanguage, get().locale);
    writeStoredLocale(nextLocale);
    set((state) => ({
      locale: nextLocale,
      needsOnboarding: false,
      bootstrapError: null,
      profile: savedProfile,
      dashboard: state.dashboard ? { ...state.dashboard, profile: savedProfile } : state.dashboard,
    }));
    await get().bootstrap();
  },
  saveProviderPreference: async (providerType, enabled) => {
    const currentStatus = get().providers.find((provider) => provider.type === providerType);
    if (!currentStatus) {
      return;
    }

    const savedPreference = await apiClient.saveProviderPreference(providerType, {
      selectedProvider: currentStatus.key,
      enabled,
      settings: {},
    });

    set((state) => ({
      providerPreferences: [
        ...state.providerPreferences.filter((preference) => preference.providerType !== providerType),
        savedPreference,
      ],
    }));
  },
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
    const activeLessonRunId = get().activeLessonRunId ?? (await apiClient.getActiveLessonRun())?.runId;
    if (!activeLessonRunId) {
      return;
    }

    await apiClient.discardLessonRun(activeLessonRunId);
    const dashboard = await apiClient.getDashboardData();
    set({
      lesson: null,
      lastLessonResult: null,
      activeLessonRunId: null,
      selectedBlockIndex: 0,
      blockResponses: {},
      blockScores: {},
      listeningTranscriptReveals: {},
      dashboard,
    });
  },
  restartLesson: async () => {
    const activeLessonRunId = get().activeLessonRunId ?? (await apiClient.getActiveLessonRun())?.runId;
    let lessonRun;
    if (activeLessonRunId) {
      lessonRun = await apiClient.restartLessonRun(activeLessonRunId);
    } else {
      lessonRun = await apiClient.startLessonRun();
    }

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
    const lesson = get().lesson;
    const activeLessonRunId = get().activeLessonRunId;
    const selectedBlockIndex = get().selectedBlockIndex;
    if (!lesson || !activeLessonRunId) {
      return;
    }

    const activeBlock = lesson.blocks[selectedBlockIndex];
    const responseText = get().blockResponses[activeBlock.id] ?? "";
    const score = buildBlockScore({
      lessonType: lesson.lessonType,
      block: activeBlock,
      responseText,
      explicitScore: get().blockScores[activeBlock.id],
      transcriptRevealed: get().listeningTranscriptReveals[activeBlock.id],
    });
    const lessonRun = await apiClient.submitBlockResult(activeLessonRunId, {
      blockId: activeBlock.id,
      userResponseType: responseText.trim() ? "text" : "none",
      userResponse: responseText,
      feedbackSummary:
        activeBlock.blockType === "listening_block" && get().listeningTranscriptReveals[activeBlock.id]
          ? `Saved from lesson runner at step ${selectedBlockIndex + 1}. Transcript support was used for this listening block.`
          : `Saved from lesson runner at step ${selectedBlockIndex + 1}.`,
      score,
    });
    set((state) => ({
      ...hydrateLessonRunState(lessonRun),
      lastLessonResult: state.lastLessonResult,
      blockResponses: {
        ...state.blockResponses,
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
    const lesson = get().lesson;
    const activeLessonRunId = get().activeLessonRunId;
    if (!lesson || !activeLessonRunId) {
      return;
    }

    const previousProgress = get().progress;
    const previousRoadmap = get().diagnosticRoadmap;
    const transcriptReveals = get().listeningTranscriptReveals;
    const explicitScores = get().blockScores;
    const blockResults: BlockResultSubmission[] = lesson.blocks.map((block, index) => {
      const responseText = get().blockResponses[block.id] ?? "";
      const blockScore = buildBlockScore({
        lessonType: lesson.lessonType,
        block,
        responseText,
        explicitScore: explicitScores[block.id],
        transcriptRevealed: transcriptReveals[block.id],
      });
      return {
        blockId: block.id,
        userResponseType: responseText.trim() ? "text" : "none",
        userResponse: responseText,
        feedbackSummary:
          block.blockType === "listening_block" && transcriptReveals[block.id]
            ? `Block ${index + 1} completed in lesson runner. Transcript support was used for this listening block.`
            : `Block ${index + 1} completed in lesson runner.`,
        score: blockScore,
      };
    });
    const overallScore =
      blockResults.length > 0
        ? Math.round(blockResults.reduce((total, block) => total + (block.score ?? 0), 0) / blockResults.length)
        : 78;
    const response = await apiClient.completeLessonRun(activeLessonRunId, overallScore, lesson.duration, blockResults);
    const [dashboard, mistakes, diagnosticRoadmap] = await Promise.all([
      apiClient.getDashboardData(),
      apiClient.getMistakes(),
      apiClient.getDiagnosticRoadmap(),
    ]);
    const resultSummary: LessonResultSummary = {
      runId: response.lessonRun.runId,
      title: response.lessonRun.lesson.title,
      score: response.lessonRun.score ?? 78,
      completedAt: response.lessonRun.completedAt,
      completedBlocks: response.lessonRun.blockRuns.filter((blockRun) => blockRun.status === "completed").length,
      totalBlocks: response.lessonRun.lesson.blocks.length,
      mistakes: response.mistakes,
      progressBefore: previousProgress,
      progressAfter: response.progress,
      nextRecommendationTitle: dashboard.recommendation.title,
      nextRecommendationGoal: dashboard.recommendation.goal,
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
      checkpointSkillInsights:
        lesson.lessonType === "diagnostic"
          ? lesson.blocks
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
              .filter((item): item is NonNullable<typeof item> => item !== null)
          : undefined,
    };
    set({
      lesson: { ...response.lessonRun.lesson, completed: true, score: response.lessonRun.score ?? 78 },
      lastLessonResult: resultSummary,
      activeLessonRunId: null,
      blockResponses: {},
      blockScores: {},
      listeningTranscriptReveals: {},
      progress: response.progress,
      diagnosticRoadmap,
      dashboard,
      mistakes: response.mistakes.length > 0 ? response.mistakes : mistakes,
    });
  },
}));

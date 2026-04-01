import { readStoredLocale } from "../i18n/locale";
import type { AppStoreData } from "./app-store.types";

type LessonRunStateSnapshot = Pick<
  AppStoreData,
  | "lesson"
  | "lastLessonResult"
  | "activeLessonRunId"
  | "selectedBlockIndex"
  | "blockResponses"
  | "blockScores"
  | "listeningTranscriptReveals"
>;

type OnboardingResetState = Pick<
  AppStoreData,
  | "isBootstrapping"
  | "bootstrapError"
  | "needsOnboarding"
  | "currentUser"
  | "currentOnboarding"
  | "profile"
  | "dashboard"
  | "mistakes"
  | "progress"
  | "diagnosticRoadmap"
  | "providerPreferences"
> &
  LessonRunStateSnapshot;

export function createEmptyLessonRunState(): LessonRunStateSnapshot {
  return {
    lesson: null,
    lastLessonResult: null,
    activeLessonRunId: null,
    selectedBlockIndex: 0,
    blockResponses: {},
    blockScores: {},
    listeningTranscriptReveals: {},
  };
}

export function createOnboardingRequiredState(
  overrides: Partial<Pick<OnboardingResetState, "currentOnboarding" | "currentUser">> = {},
): OnboardingResetState {
  return {
    isBootstrapping: false,
    bootstrapError: null,
    needsOnboarding: true,
    currentUser: null,
    currentOnboarding: null,
    profile: null,
    dashboard: null,
    ...createEmptyLessonRunState(),
    mistakes: [],
    progress: null,
    diagnosticRoadmap: null,
    providerPreferences: [],
    ...overrides,
  };
}

export function createInitialAppStoreState(): AppStoreData {
  return {
    locale: readStoredLocale() ?? "ru",
    isBootstrapping: false,
    bootstrapError: null,
    needsOnboarding: false,
    currentUser: null,
    currentOnboarding: null,
    profile: null,
    dashboard: null,
    ...createEmptyLessonRunState(),
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
  };
}

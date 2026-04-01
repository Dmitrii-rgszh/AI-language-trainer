import type { UserAccount, UserAccountDraft } from "../../entities/account/model";
import type { BlockResultSubmission, Lesson, LessonResultSummary } from "../../entities/lesson/model";
import type { Mistake } from "../../entities/mistake/model";
import type { CompleteOnboardingRequest, UserOnboarding } from "../../entities/onboarding/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import type { UserProfile } from "../../entities/user/model";
import type { AppLocale } from "../i18n/locale";
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

export interface AppStoreData {
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
}

export interface AppStoreActions {
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

export interface AppState extends AppStoreData, AppStoreActions {}

export type AppStoreSet = (
  partial: Partial<AppState> | ((state: AppState) => Partial<AppState>),
) => void;

export type AppStoreGet = () => AppState;

export type AppStoreActionKey = keyof AppStoreActions;

export type LessonBlockResultBuilder = (params: {
  blockId: string;
  blockIndex: number;
  explicitScore?: number;
  lesson: Lesson;
  responseText: string;
  transcriptRevealed: boolean;
}) => BlockResultSubmission;

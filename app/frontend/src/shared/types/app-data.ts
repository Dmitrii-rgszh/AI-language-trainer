import type { LessonRecommendation } from "../../entities/lesson/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import type { UserProfile } from "../../entities/user/model";
import type { WeakSpot } from "../../entities/mistake/model";
import type { VocabularyItem } from "../../entities/vocabulary/model";

export interface QuickAction {
  id: string;
  title: string;
  description: string;
  route: string;
}

export interface ResumeLessonCard {
  runId: string;
  title: string;
  currentBlockTitle: string;
  completedBlocks: number;
  totalBlocks: number;
  route: string;
}

export interface DashboardData {
  profile: UserProfile;
  progress: ProgressSnapshot;
  weakSpots: WeakSpot[];
  recommendation: LessonRecommendation;
  studyLoop: AdaptiveStudyLoop | null;
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  quickActions: QuickAction[];
  resumeLesson: ResumeLessonCard | null;
}

export interface DailyLoopStep {
  id: string;
  skill: string;
  title: string;
  description: string;
  durationMinutes: number;
}

export interface DailyLoopPlan {
  id: string;
  planDateKey: string;
  status: string;
  stage: string;
  sessionKind: string;
  focusArea: string;
  headline: string;
  summary: string;
  whyThisNow: string;
  nextStepHint: string;
  preferredMode: string;
  timeBudgetMinutes: number;
  estimatedMinutes: number;
  recommendedLessonType: string;
  recommendedLessonTitle: string;
  lessonRunId?: string | null;
  completedAt?: string | null;
  steps: DailyLoopStep[];
}

export interface JourneyTomorrowPreview {
  focusArea: string;
  sessionKind: string;
  headline: string;
  reason: string;
  nextStepHint: string;
  recommendedLessonTitle?: string | null;
  continuityMode?: string | null;
  carryOverSignalLabel?: string | null;
  watchSignalLabel?: string | null;
}

export interface JourneyCompletedLessonSignal {
  lessonTitle?: string | null;
  lessonType?: string | null;
  score?: number | null;
  completedAt?: string | null;
}

export interface JourneyPracticeMixEvaluation {
  leadPracticeKey?: string | null;
  leadPracticeTitle?: string | null;
  leadOutcome?: string | null;
  leadAverageScore?: number | null;
  strongestPracticeKey?: string | null;
  strongestPracticeTitle?: string | null;
  strongestPracticeScore?: number | null;
  weakestPracticeKey?: string | null;
  weakestPracticeTitle?: string | null;
  weakestPracticeScore?: number | null;
  summaryLine?: string | null;
}

export interface SkillTrajectorySignal {
  skill: string;
  direction: string;
  deltaScore: number;
  currentScore: number;
  summary: string;
}

export interface SkillTrajectoryMemory {
  focusSkill: string;
  direction: string;
  summary: string;
  observedSnapshots: number;
  signals: SkillTrajectorySignal[];
}

export interface JourneySessionSummary {
  outcomeBand: string;
  headline: string;
  whatWorked: string;
  watchSignal: string;
  strategyShift: string;
  coachNote: string;
  carryOverSignalLabel?: string | null;
  watchSignalLabel?: string | null;
  weakSpotTitle?: string | null;
  strongestSignalLabel?: string | null;
  weakestSignalLabel?: string | null;
  practiceMixEvaluation?: JourneyPracticeMixEvaluation | null;
}

export interface JourneyActivePlanSeed {
  source?: string | null;
  planDateKey?: string | null;
  focusArea?: string | null;
  sessionKind?: string | null;
}

export interface JourneyStrategySnapshot {
  primaryGoal?: string;
  preferredMode?: string;
  diagnosticReadiness?: string;
  timeBudgetMinutes?: number;
  focusArea?: string;
  activeSkillFocus?: string[];
  proofLessonDirections?: string[];
  recommendationTitle?: string | null;
  recommendationType?: string | null;
  tomorrowPreview?: JourneyTomorrowPreview | null;
  completedLesson?: JourneyCompletedLessonSignal | null;
  sessionSummary?: JourneySessionSummary | null;
  skillTrajectory?: SkillTrajectoryMemory | null;
  activePlanSeed?: JourneyActivePlanSeed | null;
}

export interface LearnerJourneyState {
  userId: string;
  stage: string;
  source: string;
  preferredMode: string;
  diagnosticReadiness: string;
  timeBudgetMinutes: number;
  currentFocusArea: string;
  currentStrategySummary: string;
  nextBestAction: string;
  lastDailyPlanId?: string | null;
  strategySnapshot: JourneyStrategySnapshot;
  onboardingCompletedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AdaptiveLoopStep {
  id: string;
  title: string;
  description: string;
  route: string;
  stepType: string;
}

export interface ModuleRotationItem {
  moduleKey: string;
  title: string;
  reason: string;
  route: string;
  priority: number;
}

export interface VocabularyReviewItem extends VocabularyItem {
  sourceModule: string;
  reviewReason: string;
  linkedMistakeSubtype?: string | null;
  linkedMistakeTitle?: string | null;
  dueNow: boolean;
}

export interface MistakeVocabularyBacklink {
  weakSpotTitle: string;
  weakSpotCategory: string;
  dueCount: number;
  activeCount: number;
  exampleWords: string[];
  sourceModules: string[];
}

export interface MistakeResolutionSignal {
  weakSpotTitle: string;
  weakSpotCategory: string;
  status: "active" | "recovering" | "stabilizing" | string;
  repetitionCount: number;
  lastSeenDaysAgo: number;
  linkedVocabularyCount: number;
  resolutionHint: string;
}

export interface AdaptiveStrategyAlignment {
  focusArea: string;
  routeTitle: string;
  routeSeedSource: string;
  routeSeedDetail: string;
  whyNow: string;
  nextBestAction: string;
  carryOverSignalLabel?: string | null;
  watchSignalLabel?: string | null;
  recommendedModuleKey?: string | null;
  recommendedModuleReason?: string | null;
  liveProgressFocus?: string | null;
  liveProgressScore?: number | null;
  liveProgressReason?: string | null;
  skillTrajectory?: SkillTrajectoryMemory | null;
}

export interface AdaptiveStudyLoop {
  focusArea: string;
  headline: string;
  summary: string;
  recommendation: LessonRecommendation;
  weakSpots: WeakSpot[];
  dueVocabulary: VocabularyReviewItem[];
  vocabularyBacklinks: MistakeVocabularyBacklink[];
  mistakeResolution: MistakeResolutionSignal[];
  moduleRotation: ModuleRotationItem[];
  vocabularySummary: {
    dueCount: number;
    newCount: number;
    activeCount: number;
    masteredCount: number;
    weakestCategory?: string | null;
  };
  listeningFocus?: string | null;
  generationRationale: string[];
  nextSteps: AdaptiveLoopStep[];
  strategyAlignment?: AdaptiveStrategyAlignment | null;
}

export interface VocabularyHub {
  summary: {
    dueCount: number;
    newCount: number;
    activeCount: number;
    masteredCount: number;
    weakestCategory?: string | null;
  };
  dueItems: VocabularyReviewItem[];
  recentItems: VocabularyReviewItem[];
  mistakeBacklinks: MistakeVocabularyBacklink[];
}

export interface ListeningAttempt {
  id: string;
  lessonRunId: string;
  lessonTitle: string;
  blockTitle: string;
  promptLabel?: string | null;
  answerSummary: string;
  score: number;
  usedTranscriptSupport: boolean;
  completedAt: string;
}

export interface ListeningTrend {
  averageScore: number;
  recentAttempts: number;
  transcriptSupportRate: number;
  weakestPrompts: Array<{
    label: string;
    occurrences: number;
  }>;
}

export interface LevelMilestone {
  level: string;
  status: string;
  readiness: number;
  requiredScore: number;
  currentScore: number;
  description: string;
  focusSkills: string[];
}

export interface DiagnosticRoadmap {
  declaredCurrentLevel: string;
  estimatedLevel: string;
  targetLevel: string;
  overallScore: number;
  summary: string;
  weakestSkills: string[];
  nextFocus: string[];
  milestones: LevelMilestone[];
}

export interface GrammarTopic {
  id: string;
  title: string;
  level: string;
  mastery: number;
  explanation: string;
  checkpoints: string[];
}

export interface SpeakingScenario {
  id: string;
  title: string;
  mode: "guided" | "free" | "roleplay";
  goal: string;
  prompt: string;
  feedbackHint: string;
}

export interface PronunciationDrill {
  id: string;
  title: string;
  sound: string;
  focus: string;
  phrases: string[];
  difficulty: string;
}

export interface PronunciationAssessment {
  targetText: string;
  transcript: string;
  score: number;
  matchedTokens: string[];
  missedTokens: string[];
  feedback: string;
  weakestWords: string[];
  wordAssessments: Array<{
    targetWord: string;
    heardWord?: string | null;
    score: number;
    status: string;
    note: string;
  }>;
  focusAssessments: Array<{
    focus: string;
    status: string;
    note: string;
  }>;
}

export interface PronunciationAttempt {
  id: string;
  drillId?: string | null;
  drillTitle?: string | null;
  targetText: string;
  soundFocus?: string | null;
  transcript: string;
  score: number;
  feedback: string;
  weakestWords: string[];
  focusIssues: string[];
  createdAt: string;
}

export interface PronunciationTrend {
  averageScore: number;
  recentAttempts: number;
  weakestWords: Array<{
    label: string;
    occurrences: number;
  }>;
  weakestSounds: Array<{
    label: string;
    occurrences: number;
  }>;
}

export interface WritingTask {
  id: string;
  title: string;
  brief: string;
  tone: string;
  checklist: string[];
  improvedVersionPreview: string;
}

export interface WritingAttempt {
  id: string;
  taskId: string;
  taskTitle: string;
  draft: string;
  feedbackSummary: string;
  feedbackSource: "ai" | "mock";
  voiceText: string;
  voiceLanguage: "ru" | "en";
  createdAt: string;
}

export interface ProfessionTrackCard {
  id: string;
  title: string;
  domain: string;
  summary: string;
  lessonFocus: string[];
}

export interface ProviderStatus {
  key: string;
  name: string;
  type: "llm" | "stt" | "tts" | "scoring";
  status: "ready" | "mock" | "offline";
  details: string;
}

export interface ProviderPreference {
  providerType: "llm" | "stt" | "tts" | "scoring";
  selectedProvider: string;
  enabled: boolean;
  settings: Record<string, unknown>;
}

export interface WelcomeTutorStatus {
  available: boolean;
  mode: "musetalk" | "fallback";
  details: string;
}

export interface AITextFeedback {
  source: "ai" | "mock";
  summary: string;
  voiceText: string;
  voiceLanguage: "ru" | "en";
}

export interface SpeakingVoiceFeedback {
  transcript: string;
  feedback: AITextFeedback;
}

export interface SpeakingAttempt {
  id: string;
  scenarioId: string;
  scenarioTitle: string;
  inputMode: "text" | "voice";
  transcript: string;
  feedbackSummary: string;
  feedbackSource: "ai" | "mock";
  voiceText: string;
  voiceLanguage: "ru" | "en";
  createdAt: string;
}

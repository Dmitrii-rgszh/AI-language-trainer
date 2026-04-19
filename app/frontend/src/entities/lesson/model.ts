export type LessonType =
  | "core"
  | "diagnostic"
  | "grammar"
  | "speaking"
  | "pronunciation"
  | "writing"
  | "professional"
  | "mixed"
  | "recovery";

export type LessonBlockType =
  | "intro_block"
  | "review_block"
  | "grammar_block"
  | "vocab_block"
  | "speaking_block"
  | "pronunciation_block"
  | "listening_block"
  | "reading_block"
  | "writing_block"
  | "profession_block"
  | "reflection_block"
  | "summary_block";

export interface LessonBlock {
  id: string;
  blockType: LessonBlockType;
  title: string;
  instructions: string;
  estimatedMinutes: number;
  payload: Record<string, unknown>;
}

export interface Lesson {
  id: string;
  lessonType: LessonType;
  title: string;
  goal: string;
  difficulty: string;
  duration: number;
  modules: LessonBlockType[];
  blocks: LessonBlock[];
  completed: boolean;
  score?: number;
}

export interface LessonRecommendation {
  id: string;
  title: string;
  lessonType: LessonType;
  goal: string;
  duration: number;
  focusArea: string;
}

export interface LessonRunState {
  runId: string;
  status: string;
  startedAt: string;
  completedAt?: string;
  score?: number;
  lesson: Lesson;
  blockRuns: LessonBlockRunState[];
}

export interface LessonBlockRunState {
  id: string;
  blockId: string;
  status: string;
  userResponseType: string;
  userResponse?: string;
  transcript?: string;
  feedbackSummary?: string;
  score?: number;
}

export interface BlockResultSubmission {
  blockId: string;
  userResponseType: "none" | "text" | "voice" | "multiple_choice";
  userResponse?: string;
  transcript?: string;
  feedbackSummary?: string;
  score?: number;
}

export interface CompleteLessonRunResponse {
  lessonRun: LessonRunState;
  progress: import("../progress/model").ProgressSnapshot;
  mistakes: import("../mistake/model").Mistake[];
}

export interface LessonResultSummary {
  runId: string;
  title: string;
  score: number;
  completedAt?: string;
  completedBlocks: number;
  totalBlocks: number;
  mistakes: import("../mistake/model").Mistake[];
  progressBefore?: import("../progress/model").ProgressSnapshot | null;
  progressAfter: import("../progress/model").ProgressSnapshot;
  nextRecommendationTitle?: string;
  nextRecommendationGoal?: string;
  diagnosticEstimatedLevelBefore?: string;
  diagnosticEstimatedLevelAfter?: string;
  diagnosticOverallScoreBefore?: number;
  diagnosticOverallScoreAfter?: number;
  milestoneDeltas?: Array<{
    level: string;
    readinessBefore: number;
    readinessAfter: number;
  }>;
  checkpointSkillInsights?: Array<{
    skill: string;
    checkpointScore: number;
    note: string;
  }>;
}

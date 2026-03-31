import type {
  BlockResultSubmission,
  CompleteLessonRunResponse,
  Lesson,
  LessonRecommendation,
  LessonRunState,
} from "../../entities/lesson/model";
import type { Mistake } from "../../entities/mistake/model";
import type {
  CompleteOnboardingRequest,
  CompleteOnboardingResponse,
  UserOnboarding,
} from "../../entities/onboarding/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import type { UserAccount } from "../../entities/account/model";
import type { UserProfile } from "../../entities/user/model";
import { readStoredActiveUserId } from "../auth/active-user";
import type {
  AITextFeedback,
  AdaptiveStudyLoop,
  DashboardData,
  DiagnosticRoadmap,
  GrammarTopic,
  ListeningAttempt,
  ListeningTrend,
  ProfessionTrackCard,
  PronunciationDrill,
  PronunciationAttempt,
  PronunciationTrend,
  ProviderPreference,
  ProviderStatus,
  PronunciationAssessment,
  SpeakingAttempt,
  SpeakingScenario,
  SpeakingVoiceFeedback,
  VocabularyReviewItem,
  VocabularyHub,
  WritingAttempt,
  WritingTask,
} from "../types/app-data";

export class ApiError extends Error {
  readonly status: number;
  readonly path: string;

  constructor(status: number, path: string, message?: string) {
    super(message ?? `Request failed: ${status} for ${path}`);
    this.name = "ApiError";
    this.status = status;
    this.path = path;
  }
}

function buildRequestInit(init?: RequestInit, attachActiveUser = true): RequestInit | undefined {
  const headers = new Headers(init?.headers);
  const activeUserId = attachActiveUser ? readStoredActiveUserId() : null;
  if (activeUserId) {
    headers.set("X-User-Id", activeUserId);
  }

  return {
    ...init,
    headers,
  };
}

async function request<T>(path: string, init?: RequestInit, attachActiveUser = true): Promise<T> {
  const response = await fetch(path, buildRequestInit(init, attachActiveUser));
  if (!response.ok) {
    throw new ApiError(response.status, path);
  }

  return (await response.json()) as T;
}

async function requestBlob(path: string, init?: RequestInit): Promise<Blob> {
  const response = await fetch(path, buildRequestInit(init));
  if (!response.ok) {
    throw new ApiError(response.status, path);
  }

  return await response.blob();
}

export const apiClient = {
  getDashboardData: () => request<DashboardData>("/api/dashboard"),
  getAdaptiveStudyLoop: () => request<AdaptiveStudyLoop>("/api/adaptive/loop"),
  getVocabularyHub: () => request<VocabularyHub>("/api/adaptive/vocabulary/hub"),
  getDiagnosticRoadmap: () => request<DiagnosticRoadmap>("/api/diagnostic/roadmap"),
  startDiagnosticCheckpoint: () =>
    request<LessonRunState>("/api/diagnostic/checkpoint-run", {
      method: "POST",
    }),
  startRecoveryRun: () =>
    request<LessonRunState>("/api/adaptive/recovery-run", {
      method: "POST",
    }),
  reviewVocabularyItem: (itemId: string, successful = true) =>
    request<VocabularyReviewItem>(`/api/adaptive/vocabulary/${itemId}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ successful }),
    }),
  getCurrentUser: () => request<UserAccount>("/api/users/me"),
  saveCurrentUser: (payload: { login: string; email: string }) =>
    request<UserAccount>("/api/users/me", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getCurrentOnboarding: () => request<UserOnboarding>("/api/onboarding/current"),
  completeOnboarding: (payload: CompleteOnboardingRequest) =>
    request<CompleteOnboardingResponse>(
      "/api/onboarding/complete",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      false,
    ),
  getProfile: () => request<UserProfile>("/api/profile"),
  saveProfile: (profile: UserProfile) =>
    request<UserProfile>("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    }),
  getRecommendedLesson: () => request<LessonRecommendation>("/api/recommendations/next"),
  getLesson: () => request<Lesson>("/api/lessons/recommended"),
  startLessonRun: (templateId?: string) =>
    request<LessonRunState>("/api/lessons/runs/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ templateId: templateId ?? null }),
    }),
  getActiveLessonRun: () => request<LessonRunState | null>("/api/lessons/runs/active"),
  discardLessonRun: async (runId: string) => {
    const response = await fetch(`/api/lessons/runs/${runId}`, { method: "DELETE" });
    if (!response.ok) {
      throw new ApiError(response.status, `/api/lessons/runs/${runId}`);
    }
  },
  restartLessonRun: (runId: string) =>
    request<LessonRunState>(`/api/lessons/runs/${runId}/restart`, {
      method: "POST",
    }),
  submitBlockResult: (runId: string, payload: BlockResultSubmission) =>
    request<LessonRunState>(`/api/lessons/runs/${runId}/blocks/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  completeLessonRun: (
    runId: string,
    score: number,
    minutesCompleted?: number,
    blockResults: BlockResultSubmission[] = [],
  ) =>
    request<CompleteLessonRunResponse>(`/api/lessons/runs/${runId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        score,
        minutesCompleted: minutesCompleted ?? null,
        blockResults,
      }),
    }),
  getGrammarTopics: () => request<GrammarTopic[]>("/api/grammar/topics"),
  getSpeakingScenarios: () => request<SpeakingScenario[]>("/api/speaking/scenarios"),
  getSpeakingFeedback: (payload: { scenarioId: string; transcript: string; feedbackLanguage?: "ru" | "en" }) =>
    request<AITextFeedback>("/api/speaking/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getSpeakingAttempts: () => request<SpeakingAttempt[]>("/api/speaking/attempts"),
  getListeningHistory: () => request<ListeningAttempt[]>("/api/listening/history"),
  getListeningTrends: () => request<ListeningTrend>("/api/listening/trends"),
  getSpeakingVoiceFeedback: (payload: {
    scenarioId: string;
    audio: Blob;
    feedbackLanguage?: "ru" | "en";
  }) => {
    const formData = new FormData();
    formData.append("scenario_id", payload.scenarioId);
    formData.append("feedback_language", payload.feedbackLanguage ?? "ru");
    formData.append("audio", payload.audio, "speaking.webm");

    return request<SpeakingVoiceFeedback>("/api/speaking/voice-feedback", {
      method: "POST",
      body: formData,
    });
  },
  getPronunciationDrills: () => request<PronunciationDrill[]>("/api/pronunciation/drills"),
  getPronunciationAttempts: () => request<PronunciationAttempt[]>("/api/pronunciation/attempts"),
  getPronunciationTrends: () => request<PronunciationTrend>("/api/pronunciation/trends"),
  assessPronunciation: (payload: { targetText: string; audio: Blob; drillId?: string; soundFocus?: string }) => {
    const formData = new FormData();
    formData.append("target_text", payload.targetText);
    if (payload.drillId) {
      formData.append("drill_id", payload.drillId);
    }
    if (payload.soundFocus) {
      formData.append("sound_focus", payload.soundFocus);
    }
    formData.append("audio", payload.audio, "pronunciation.webm");

    return request<PronunciationAssessment>("/api/pronunciation/assess", {
      method: "POST",
      body: formData,
    });
  },
  getWritingTask: () => request<WritingTask>("/api/writing/task"),
  getWritingAttempts: () => request<WritingAttempt[]>("/api/writing/attempts"),
  reviewWriting: (payload: { taskId: string; draft: string; feedbackLanguage?: "ru" | "en" }) =>
    request<AITextFeedback>("/api/writing/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getProfessionTracks: () => request<ProfessionTrackCard[]>("/api/profession/tracks"),
  getMistakes: () => request<Mistake[]>("/api/mistakes"),
  getProgress: () => request<ProgressSnapshot>("/api/progress"),
  getProviders: () => request<ProviderStatus[]>("/api/providers/status"),
  getProviderPreferences: () => request<ProviderPreference[]>("/api/providers/preferences"),
  saveProviderPreference: (
    providerType: ProviderPreference["providerType"],
    payload: Omit<ProviderPreference, "providerType">,
  ) =>
    request<ProviderPreference>(`/api/providers/preferences/${providerType}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  synthesizeSpeech: (payload: {
    text: string;
    language?: string;
    speaker?: string | null;
    style?: "coach" | "warm" | "neutral";
  }) =>
    requestBlob("/api/voice/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};

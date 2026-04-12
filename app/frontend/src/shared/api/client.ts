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
import type { LoginAvailability, UserAccount } from "../../entities/account/model";
import type { UserProfile } from "../../entities/user/model";
import { readStoredActiveUserId } from "../auth/active-user";
import type {
  LiveAvatarConfig,
  LiveAvatarFallbackResponse,
  LiveAvatarStatus,
} from "../types/live-avatar";
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
  WelcomeTutorStatus,
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

const welcomeTutorClipCache = new Map<string, Promise<Blob>>();
const WELCOME_TUTOR_CLIP_CACHE_SCHEMA = "v5-idle-motion-signature";
const liveAvatarPresenceVideoCache = new Map<string, Promise<Blob>>();
const welcomeReplayAudioCache = new Map<string, Promise<Blob>>();
const welcomeProofLessonCueAudioCache = new Map<string, Promise<Blob>>();
const welcomeTutorPresetClipCache = new Map<string, Promise<Blob>>();
const WELCOME_TUTOR_PRESET_CACHE_SCHEMA = "welcome-presets-v7-stable-coach";

function buildWelcomeTutorClipCacheKey(payload: {
  text: string;
  language: "ru" | "en";
  avatarKey?: string;
  cacheSignature?: string;
}) {
  return [
    WELCOME_TUTOR_CLIP_CACHE_SCHEMA,
    payload.avatarKey ?? "verba_tutor",
    payload.language,
    payload.text.trim(),
    payload.cacheSignature?.trim() || "tts-unknown",
  ].join("|");
}

function getWelcomeTutorClip(payload: {
  text: string;
  language: "ru" | "en";
  avatarKey?: string;
  cacheSignature?: string;
}) {
  const cacheKey = buildWelcomeTutorClipCacheKey(payload);
  const cachedRequest = welcomeTutorClipCache.get(cacheKey);
  if (cachedRequest) {
    return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  }

  const nextRequest = requestBlob("/api/welcome/ai-tutor/video", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: payload.text,
      language: payload.language,
      avatar_key: payload.avatarKey ?? "verba_tutor",
    }),
  }).catch((error) => {
    welcomeTutorClipCache.delete(cacheKey);
    throw error;
  });

  welcomeTutorClipCache.set(cacheKey, nextRequest);
  return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
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
  checkLoginAvailability: (payload: { login: string; email?: string }) =>
    request<LoginAvailability>(
      `/api/users/login-availability?${new URLSearchParams(
        payload.email ? { login: payload.login, email: payload.email } : { login: payload.login },
      ).toString()}`,
      undefined,
      false,
    ),
  signIn: (payload: { login: string; email: string }) =>
    request<UserAccount>(
      "/api/users/sign-in",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      false,
    ),
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
  assessPronunciation: (payload: {
    targetText: string;
    audio: Blob;
    drillId?: string;
    soundFocus?: string;
    language?: "ru" | "en";
  }) => {
    const formData = new FormData();
    formData.append("target_text", payload.targetText);
    if (payload.drillId) {
      formData.append("drill_id", payload.drillId);
    }
    if (payload.soundFocus) {
      formData.append("sound_focus", payload.soundFocus);
    }
    if (payload.language) {
      formData.append("language", payload.language);
    }
    formData.append("audio", payload.audio, "pronunciation.webm");

    return request<PronunciationAssessment>("/api/pronunciation/assess", {
      method: "POST",
      body: formData,
    });
  },
  assessWelcomePronunciation: (payload: {
    targetText: string;
    audio: Blob;
    language?: "ru" | "en";
  }) => {
    const formData = new FormData();
    formData.append("target_text", payload.targetText);
    if (payload.language) {
      formData.append("language", payload.language);
    }
    formData.append("audio", payload.audio, "welcome-proof-lesson.webm");

    return request<PronunciationAssessment>(
      "/api/welcome/pronunciation-assess",
      {
        method: "POST",
        body: formData,
      },
      false,
    );
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
  getWelcomeTutorStatus: () => request<WelcomeTutorStatus>("/api/welcome/ai-tutor/status"),
  getProviderPreferences: () => request<ProviderPreference[]>("/api/providers/preferences"),
  getLiveAvatarConfig: () => request<LiveAvatarConfig>("/api/live-avatar/config"),
  getLiveAvatarStatus: () => request<LiveAvatarStatus>("/api/live-avatar/status"),
  getLiveAvatarIdleLoopUrl: (avatarKey?: string, revision?: string) => {
    const searchParams = new URLSearchParams();
    if (avatarKey) {
      searchParams.set("avatar_key", avatarKey);
    }
    if (revision) {
      searchParams.set("rev", revision);
    }
    const query = searchParams.toString();
    return query ? `/api/live-avatar/idle-loop?${query}` : "/api/live-avatar/idle-loop";
  },
  getLiveAvatarIdleLoopBlob: (avatarKey?: string, revision?: string) => {
    const path = apiClient.getLiveAvatarIdleLoopUrl(avatarKey, revision);
    return requestBlob(path);
  },
  getLiveAvatarPresenceVideoUrl: (avatarKey?: string, revision?: string) => {
    const searchParams = new URLSearchParams();
    if (avatarKey) {
      searchParams.set("avatar_key", avatarKey);
    }
    if (revision) {
      searchParams.set("rev", revision);
    }
    const query = searchParams.toString();
    return query ? `/api/live-avatar/presence-video?${query}` : "/api/live-avatar/presence-video";
  },
  getLiveAvatarPresenceVideoBlob: (avatarKey?: string, revision?: string) => {
    const cacheKey = `${avatarKey?.trim() || "verba_tutor"}|${revision?.trim() || "current"}`;
    const cachedRequest = liveAvatarPresenceVideoCache.get(cacheKey);
    if (cachedRequest) {
      return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
    }

    const nextRequest = requestBlob(apiClient.getLiveAvatarPresenceVideoUrl(avatarKey, revision)).catch((error) => {
      liveAvatarPresenceVideoCache.delete(cacheKey);
      throw error;
    });

    liveAvatarPresenceVideoCache.set(cacheKey, nextRequest);
    return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  },
  preloadLiveAvatarPresenceVideo: async (avatarKey?: string, revision?: string) => {
    await apiClient.getLiveAvatarPresenceVideoBlob(avatarKey, revision);
  },
  getWelcomeReplayAudioUrl: (locale: "ru" | "en") => `/api/voice/welcome-replay?locale=${locale}`,
  getWelcomeReplayAudioBlob: (locale: "ru" | "en") => {
    const cachedRequest = welcomeReplayAudioCache.get(locale);
    if (cachedRequest) {
      return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
    }

    const nextRequest = requestBlob(apiClient.getWelcomeReplayAudioUrl(locale)).catch((error) => {
      welcomeReplayAudioCache.delete(locale);
      throw error;
    });

    welcomeReplayAudioCache.set(locale, nextRequest);
    return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  },
  preloadWelcomeReplayAudio: async (locale: "ru" | "en") => {
    await apiClient.getWelcomeReplayAudioBlob(locale);
  },
  getWelcomeProofLessonCueAudioUrl: (
    locale: "ru" | "en",
    cue: "feedback" | "clarity" | "retry" | "result",
  ) => `/api/voice/welcome-proof-lesson-cue?locale=${locale}&cue=${cue}`,
  getWelcomeProofLessonCueAudioBlob: (
    locale: "ru" | "en",
    cue: "feedback" | "clarity" | "retry" | "result",
  ) => {
    const cacheKey = `${locale}:${cue}`;
    const cachedRequest = welcomeProofLessonCueAudioCache.get(cacheKey);
    if (cachedRequest) {
      return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
    }

    const nextRequest = requestBlob(apiClient.getWelcomeProofLessonCueAudioUrl(locale, cue)).catch((error) => {
      welcomeProofLessonCueAudioCache.delete(cacheKey);
      throw error;
    });

    welcomeProofLessonCueAudioCache.set(cacheKey, nextRequest);
    return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  },
  preloadWelcomeProofLessonCueAudio: async (
    locale: "ru" | "en",
    cue: "feedback" | "clarity" | "retry" | "result",
  ) => {
    await apiClient.getWelcomeProofLessonCueAudioBlob(locale, cue);
  },
  getWelcomeProofLessonModelAudioBlob: (locale: "ru" | "en") => {
    const cacheKey = `model:${locale}`;
    const cachedRequest = welcomeProofLessonCueAudioCache.get(cacheKey);
    if (cachedRequest) {
      return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
    }

    const nextRequest = apiClient.synthesizeSpeech({
      text: "I'd like a coffee without sugar.",
      language: "en",
      speaker: "Daisy Studious",
      style: "warm",
    }).catch((error) => {
      welcomeProofLessonCueAudioCache.delete(cacheKey);
      throw error;
    });

    welcomeProofLessonCueAudioCache.set(cacheKey, nextRequest);
    return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  },
  preloadWelcomeProofLessonModelAudio: async (locale: "ru" | "en") => {
    await apiClient.getWelcomeProofLessonModelAudioBlob(locale);
  },
  renderLiveAvatarFallback: (payload: {
    userText: string;
    language: "ru" | "en";
    avatarKey?: string;
  }) =>
    request<LiveAvatarFallbackResponse>("/api/live-avatar/fallback-render", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_text: payload.userText,
        language: payload.language,
        avatar_key: payload.avatarKey ?? "verba_tutor",
      }),
    }),
  getLiveAvatarFallbackClip: (clipId: string) =>
    requestBlob(`/api/live-avatar/fallback-render/${clipId}`),
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
  transcribeSpeech: (audio: Blob, language?: "ru" | "en") => {
    const formData = new FormData();
    formData.append("audio", audio, "welcome-proof-lesson.webm");
    if (language) {
      formData.append("language", language);
    }

    return request<{ transcript: string }>("/api/voice/transcribe", {
      method: "POST",
      body: formData,
    });
  },
  renderWelcomeTutorClip: (payload: {
    text: string;
    language: "ru" | "en";
    avatarKey?: string;
    cacheSignature?: string;
  }) => getWelcomeTutorClip(payload),
  getWelcomeTutorPresetClipUrl: (payload: {
    locale: "ru" | "en";
    kind: "intro" | "replay" | "clarity_intro" | "clarity_model";
    variant?: number;
    revision?: string;
  }) => {
    const searchParams = new URLSearchParams({
      locale: payload.locale,
      kind: payload.kind,
      variant: String(payload.variant ?? 0),
      rev: payload.revision?.trim() || WELCOME_TUTOR_PRESET_CACHE_SCHEMA,
    });
    return `/api/welcome/ai-tutor/preset-video?${searchParams.toString()}`;
  },
  getWelcomeTutorPresetClip: (payload: {
    locale: "ru" | "en";
    kind: "intro" | "replay" | "clarity_intro" | "clarity_model";
    variant?: number;
    revision?: string;
    bypassCache?: boolean;
  }) => {
    const cacheKey = [
      WELCOME_TUTOR_PRESET_CACHE_SCHEMA,
      payload.locale,
      payload.kind,
      String(payload.variant ?? 0),
      payload.revision?.trim() || WELCOME_TUTOR_PRESET_CACHE_SCHEMA,
    ].join("|");
    const cachedRequest = payload.bypassCache ? null : welcomeTutorPresetClipCache.get(cacheKey);
    if (cachedRequest) {
      return cachedRequest.then((blob) => blob.slice(0, blob.size, blob.type));
    }

    const nextRequest = requestBlob(
      apiClient.getWelcomeTutorPresetClipUrl(payload),
      payload.bypassCache ? { cache: "reload" } : undefined,
    ).catch((error) => {
      welcomeTutorPresetClipCache.delete(cacheKey);
      throw error;
    });
    if (!payload.bypassCache) {
      welcomeTutorPresetClipCache.set(cacheKey, nextRequest);
    }
    return nextRequest.then((blob) => blob.slice(0, blob.size, blob.type));
  },
  prefetchWelcomeTutorClip: async (payload: {
    text: string;
    language: "ru" | "en";
    avatarKey?: string;
    cacheSignature?: string;
  }) => {
    await getWelcomeTutorClip(payload);
  },
  prefetchWelcomeTutorPresetClip: async (payload: {
    locale: "ru" | "en";
    kind: "intro" | "replay" | "clarity_intro" | "clarity_model";
    variant?: number;
    revision?: string;
  }) => {
    await apiClient.getWelcomeTutorPresetClip(payload);
  },
};

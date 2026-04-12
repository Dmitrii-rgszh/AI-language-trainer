import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import type { AppLocale } from "../../shared/i18n/locale";
import type { PronunciationAssessment } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { writeWelcomeProofLessonHandoff } from "../../shared/profile/welcome-proof-handoff";
import { writeGuestIntent } from "./guest-intent";
import type {
  WelcomeProofLessonClarityStatusKey,
  WelcomeProofLessonInputMode,
  WelcomeProofLessonScenario,
} from "./welcomeProofLessonScenario";
import { welcomeProofLessonScenarios } from "./welcomeProofLessonScenario";

const WELCOME_PROOF_LESSON_NEXT_ROUTE = routes.onboarding;
const WELCOME_PROOF_LESSON_MIN_WORDS = 3;
const WELCOME_PROOF_LESSON_RESULT_DELAY_MS = 900;
const SMART_RECORDING_CHECK_INTERVAL_MS = 120;
const SMART_RECORDING_TRAILING_SILENCE_MS = 3000;
const SMART_RECORDING_SPEECH_CONFIRM_MS = 300;
const SMART_RECORDING_MIN_SPEECH_MS = 650;
const SMART_RECORDING_SILENCE_CONFIRM_MS = 650;
const SMART_RECORDING_FALSE_START_RESET_MS = 1400;
const SMART_RECORDING_MAX_UTTERANCE_MS = 14000;
const SMART_RECORDING_NOISE_FLOOR_DEFAULT = 0.006;
const SMART_RECORDING_START_THRESHOLD_FLOOR = 0.015;
const SMART_RECORDING_CONTINUE_THRESHOLD_FLOOR = 0.011;
const SMART_RECORDING_START_THRESHOLD_FACTOR = 3.2;
const SMART_RECORDING_CONTINUE_THRESHOLD_FACTOR = 2.2;
const SMART_RECORDING_SIGNAL_SMOOTHING = 0.45;

type WelcomeProofLessonStep =
  | "intro"
  | "situation"
  | "feedback"
  | "clarity"
  | "retry"
  | "result";

type ProofLessonResponseMode = "text" | "voice";
type WelcomeProofLessonVoiceTarget = "attempt" | "retry" | null;
type WelcomeAttemptPhase = "initial" | "recommended_repeat";
type VoiceActivityState = "idle" | "listening" | "speech_detected" | "processing";

type SmartRecordingState = {
  noiseFloor: number;
  smoothedLevel: number;
  consecutiveSpeechMs: number;
  totalSpeechMs: number;
  silenceMs: number;
  utteranceMs: number;
  hasSpeechStarted: boolean;
  lastSpeechAt: number;
};

const WELCOME_PROOF_LESSON_STEPS: WelcomeProofLessonStep[] = [
  "intro",
  "situation",
  "feedback",
  "clarity",
  "retry",
  "result",
];

function normalizeAnswer(value: string) {
  return value
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[.,!?]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function countWords(value: string) {
  return normalizeAnswer(value)
    .split(" ")
    .filter(Boolean).length;
}

function matchesAcceptedAnswer(answer: string, acceptedAnswers: string[]) {
  const normalizedAnswer = normalizeAnswer(answer);
  return acceptedAnswers.some(
    (acceptedAnswer) => normalizeAnswer(acceptedAnswer) === normalizedAnswer,
  );
}

function matchesRecommendedFirstAttempt(
  answer: string,
  recommendedAnswer: string,
) {
  const normalizedAnswer = normalizeAnswer(answer);
  const normalizedRecommended = normalizeAnswer(recommendedAnswer);

  if (normalizedAnswer === normalizedRecommended) {
    return true;
  }

  return (
    (normalizedAnswer.includes("i'd like") || normalizedAnswer.includes("i would like")) &&
    normalizedAnswer.includes("coffee") &&
    normalizedAnswer.includes("without") &&
    normalizedAnswer.includes("sugar")
  );
}

function buildClarityStatusKey(
  answer: string,
): WelcomeProofLessonClarityStatusKey {
  const normalizedAnswer = normalizeAnswer(answer);

  if (
    normalizedAnswer.includes("i'd like") &&
    normalizedAnswer.includes("coffee") &&
    normalizedAnswer.includes("without") &&
    normalizedAnswer.includes("sugar")
  ) {
    return "easy";
  }

  if (
    normalizedAnswer.includes("coffee") ||
    normalizedAnswer.includes("without") ||
    normalizedAnswer.includes("sugar")
  ) {
    return "almost";
  }

  return "needsMore";
}

function buildNextExampleScenarioIndex(
  scenarioIndex: number,
  scenarios: readonly WelcomeProofLessonScenario[],
) {
  if (scenarios.length <= 1) {
    return 0;
  }

  return (scenarioIndex + 1) % scenarios.length;
}

function buildClarityStatusKeyFromScore(score: number): WelcomeProofLessonClarityStatusKey {
  if (score >= 85) {
    return "easy";
  }
  if (score >= 65) {
    return "almost";
  }
  return "needsMore";
}

function buildPronunciationHints(
  locale: AppLocale,
  assessment: PronunciationAssessment | null,
): string[] {
  if (!assessment) {
    return locale === "ru"
      ? [
          "Автоанализ произношения не завершился, поэтому точные фонетические подсказки пока недоступны",
          "Сейчас лучше ориентироваться на общий шаблон фразы, а не на эти детали",
          "Повтори попытку, чтобы получить диагностику по словам и звукам",
        ]
      : [
          "Automatic pronunciation analysis did not finish, so precise phonetic hints are not available yet",
          "For now, rely on the general phrase pattern rather than specific sound advice",
          "Repeat the attempt to get diagnostics for words and sounds",
        ];
  }

  const hints: string[] = [];
  let hasRhythmHint = false;
  for (const focus of assessment.focusAssessments) {
    if (focus.status === "stable") {
      continue;
    }
    if (focus.focus === "th") {
      hints.push(locale === "ru" ? "Сделай звук /th/ чётче" : "Make the /th/ sound clearer");
    } else if (focus.focus === "r-coloring") {
      hints.push(locale === "ru" ? "Чётче выдели звук /r/" : "Make the /r/ sound clearer");
    } else if (focus.focus === "word rhythm") {
      hasRhythmHint = true;
      hints.push(locale === "ru" ? "Скажи фразу более слитно, без потери слов" : "Keep the phrase connected without dropping words");
    } else if (focus.focus === "word ending") {
      hints.push(locale === "ru" ? "Не съедай окончания слов" : "Do not swallow the word endings");
    }
  }

  for (const word of assessment.weakestWords) {
    const normalizedWord = word
      .toLowerCase()
      .replace(/[’']/g, "'")
      .replace(/[^a-z']/g, "")
      .trim();

    if (!normalizedWord || normalizedWord.length < 2) {
      continue;
    }

    if (["i", "a", "an"].includes(normalizedWord)) {
      continue;
    }

    if (["i'd", "id", "like", "iwould", "would"].includes(normalizedWord)) {
      if (!hasRhythmHint) {
        hints.push(
          locale === "ru"
            ? "Собери I'd like в один плавный кусок"
            : "Keep I'd like as one smooth chunk",
        );
      }
      continue;
    }

    hints.push(locale === "ru" ? `Чётче выдели ${word}` : `Stress ${word} more clearly`);
  }

  const uniqueHints = Array.from(new Set(hints)).slice(0, 3);
  if (uniqueHints.length > 0) {
    return uniqueHints;
  }

  return locale === "ru"
    ? [
        "Ключевые слова звучат уверенно",
        "Ритм фразы держится хорошо",
        "Можно говорить в том же спокойном темпе",
      ]
    : [
        "The key words sound stable",
        "The rhythm of the phrase holds together well",
        "You can keep the same calm pace",
      ];
}

export function useWelcomeProofLesson(locale: AppLocale) {
  const navigate = useNavigate();
  const scenarios = welcomeProofLessonScenarios[locale];
  const [scenarioIndex, setScenarioIndex] = useState(0);
  const [stepIndex, setStepIndex] = useState(0);
  const [attemptInputMode, setAttemptInputMode] =
    useState<WelcomeProofLessonInputMode>("voice");
  const [isAttemptActive, setIsAttemptActive] = useState(false);
  const [attemptPhase, setAttemptPhase] = useState<WelcomeAttemptPhase>("initial");
  const [attemptAnswer, setAttemptAnswer] = useState("");
  const [submittedAttemptAnswer, setSubmittedAttemptAnswer] = useState("");
  const [submittedAttemptMode, setSubmittedAttemptMode] =
    useState<ProofLessonResponseMode>("text");
  const [attemptMessage, setAttemptMessage] = useState<string | null>(null);
  const [attemptPronunciationAssessment, setAttemptPronunciationAssessment] =
    useState<PronunciationAssessment | null>(null);
  const [retryInputMode, setRetryInputMode] =
    useState<WelcomeProofLessonInputMode | null>(null);
  const [retryAnswer, setRetryAnswer] = useState("");
  const [submittedRetryAnswer, setSubmittedRetryAnswer] = useState("");
  const [submittedRetryMode, setSubmittedRetryMode] =
    useState<ProofLessonResponseMode>("text");
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retrySuccessful, setRetrySuccessful] = useState(false);
  const [isVoiceRecording, setIsVoiceRecording] = useState(false);
  const [isVoiceProcessing, setIsVoiceProcessing] = useState(false);
  const [voiceActivityState, setVoiceActivityState] =
    useState<VoiceActivityState>("idle");
  const [voiceTrailingSilenceRemainingMs, setVoiceTrailingSilenceRemainingMs] =
    useState<number | null>(null);
  const resultTimerRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const voiceTargetRef = useRef<WelcomeProofLessonVoiceTarget>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaSourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const smartRecordingIntervalRef = useRef<number | null>(null);
  const voiceStopPendingRef = useRef(false);
  const isVoiceRecordingRef = useRef(false);
  const isVoiceProcessingRef = useRef(false);
  const smartRecordingStateRef = useRef<SmartRecordingState>({
    noiseFloor: SMART_RECORDING_NOISE_FLOOR_DEFAULT,
    smoothedLevel: SMART_RECORDING_NOISE_FLOOR_DEFAULT,
    consecutiveSpeechMs: 0,
    totalSpeechMs: 0,
    silenceMs: 0,
    utteranceMs: 0,
    hasSpeechStarted: false,
    lastSpeechAt: 0,
  });
  const scenario = scenarios[scenarioIndex] ?? scenarios[0];
  const currentStep = WELCOME_PROOF_LESSON_STEPS[stepIndex] ?? "intro";
  const recommendedFirstAttempt = scenario.languageTargets.firstAttemptImproved;
  const voiceInputEnabled =
    typeof window !== "undefined" &&
    window.isSecureContext &&
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof MediaRecorder !== "undefined";

  function setVoiceRecordingState(next: boolean) {
    isVoiceRecordingRef.current = next;
    setIsVoiceRecording(next);
  }

  function setVoiceProcessingState(next: boolean) {
    isVoiceProcessingRef.current = next;
    setIsVoiceProcessing(next);
  }

  const feedback = useMemo(() => {
    const userVersion =
      submittedAttemptAnswer.trim() || scenario.languageTargets.firstAttemptImproved;
    const improvedVersion = scenario.languageTargets.firstAttemptImproved;
    const isAlreadyNatural =
      normalizeAnswer(userVersion) === normalizeAnswer(improvedVersion);

    return {
      title: isAlreadyNatural
        ? locale === "ru"
          ? "Уже звучит естественно"
          : "This already sounds natural"
        : scenario.feedback.title,
      userVersion,
      improvedVersion,
      explanationPrimary: scenario.feedback.explanationPrimary,
      explanationSecondary: scenario.feedback.explanationSecondary,
      isAlreadyNatural,
    };
  }, [locale, scenario, submittedAttemptAnswer]);

  const clarityStatusKey = useMemo(
    () =>
      submittedAttemptMode === "voice"
        ? attemptPronunciationAssessment
          ? buildClarityStatusKeyFromScore(attemptPronunciationAssessment.score)
          : "needsMore"
        : buildClarityStatusKey(submittedAttemptAnswer),
    [attemptPronunciationAssessment, submittedAttemptAnswer, submittedAttemptMode],
  );

  const clarityStatusLabel = scenario.clarity.statuses[clarityStatusKey];
  const clarityHints = useMemo(
    () =>
      submittedAttemptMode === "voice"
        ? buildPronunciationHints(locale, attemptPronunciationAssessment)
        : scenario.clarity.hints,
    [attemptPronunciationAssessment, locale, scenario.clarity.hints, submittedAttemptMode],
  );

  function clearResultTimer() {
    if (resultTimerRef.current !== null) {
      window.clearTimeout(resultTimerRef.current);
      resultTimerRef.current = null;
    }
  }

  function resetSmartRecordingState() {
    smartRecordingStateRef.current = {
      noiseFloor: SMART_RECORDING_NOISE_FLOOR_DEFAULT,
      smoothedLevel: SMART_RECORDING_NOISE_FLOOR_DEFAULT,
      consecutiveSpeechMs: 0,
      totalSpeechMs: 0,
      silenceMs: 0,
      utteranceMs: 0,
      hasSpeechStarted: false,
      lastSpeechAt: 0,
    };
    setVoiceTrailingSilenceRemainingMs(null);
  }

  function stopSmartRecordingTracking() {
    if (smartRecordingIntervalRef.current !== null) {
      window.clearInterval(smartRecordingIntervalRef.current);
      smartRecordingIntervalRef.current = null;
    }

    analyserRef.current?.disconnect();
    mediaSourceRef.current?.disconnect();
    analyserRef.current = null;
    mediaSourceRef.current = null;

    const audioContext = audioContextRef.current;
    audioContextRef.current = null;
    if (audioContext) {
      void audioContext.close().catch(() => undefined);
    }

    resetSmartRecordingState();
  }

  function computeTimeDomainRms(samples: Float32Array) {
    if (samples.length === 0) {
      return 0;
    }

    let sumSquares = 0;
    for (let index = 0; index < samples.length; index += 1) {
      const value = samples[index] ?? 0;
      sumSquares += value * value;
    }

    return Math.sqrt(sumSquares / samples.length);
  }

  function startSmartRecordingTracking(target: Exclude<WelcomeProofLessonVoiceTarget, null>) {
    stopSmartRecordingTracking();

    const stream = mediaStreamRef.current;
    if (!stream) {
      return;
    }

    const AudioContextCtor =
      window.AudioContext ||
      (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextCtor) {
      return;
    }

    try {
      const audioContext = new AudioContextCtor();
      const mediaSource = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.18;
      mediaSource.connect(analyser);

      audioContextRef.current = audioContext;
      mediaSourceRef.current = mediaSource;
      analyserRef.current = analyser;
      resetSmartRecordingState();
      setVoiceActivityState("listening");

      const samples = new Float32Array(analyser.fftSize);
      smartRecordingIntervalRef.current = window.setInterval(() => {
        if (
          voiceTargetRef.current !== target ||
          !mediaRecorderRef.current ||
          voiceStopPendingRef.current
        ) {
          return;
        }

        analyser.getFloatTimeDomainData(samples);
        const rms = computeTimeDomainRms(samples);
        const state = smartRecordingStateRef.current;
        const now = performance.now();
        state.smoothedLevel =
          state.smoothedLevel * (1 - SMART_RECORDING_SIGNAL_SMOOTHING) +
          rms * SMART_RECORDING_SIGNAL_SMOOTHING;
        const level = state.smoothedLevel;
        const startThreshold = Math.max(
          SMART_RECORDING_START_THRESHOLD_FLOOR,
          state.noiseFloor * SMART_RECORDING_START_THRESHOLD_FACTOR,
        );
        const continueThreshold = Math.max(
          SMART_RECORDING_CONTINUE_THRESHOLD_FLOOR,
          state.noiseFloor * SMART_RECORDING_CONTINUE_THRESHOLD_FACTOR,
        );

        if (!state.hasSpeechStarted) {
          if (level < startThreshold) {
            state.noiseFloor = state.noiseFloor * 0.9 + level * 0.1;
            state.consecutiveSpeechMs = Math.max(
              0,
              state.consecutiveSpeechMs - SMART_RECORDING_CHECK_INTERVAL_MS * 0.5,
            );
            setVoiceTrailingSilenceRemainingMs(null);
            setVoiceActivityState("listening");
            return;
          }

          state.consecutiveSpeechMs += SMART_RECORDING_CHECK_INTERVAL_MS;
          if (state.consecutiveSpeechMs < SMART_RECORDING_SPEECH_CONFIRM_MS) {
            return;
          }

          state.hasSpeechStarted = true;
          state.totalSpeechMs = state.consecutiveSpeechMs;
          state.utteranceMs = state.consecutiveSpeechMs;
          state.silenceMs = 0;
          state.lastSpeechAt = now;
          setVoiceTrailingSilenceRemainingMs(null);
          setVoiceActivityState("speech_detected");
          return;
        }

        state.utteranceMs += SMART_RECORDING_CHECK_INTERVAL_MS;

        if (level >= continueThreshold) {
          state.totalSpeechMs += SMART_RECORDING_CHECK_INTERVAL_MS;
          state.silenceMs = 0;
          state.lastSpeechAt = now;
          setVoiceTrailingSilenceRemainingMs(null);
          setVoiceActivityState("speech_detected");
          return;
        }

        state.silenceMs += SMART_RECORDING_CHECK_INTERVAL_MS;

        if (
          state.totalSpeechMs < SMART_RECORDING_MIN_SPEECH_MS &&
          state.silenceMs >= SMART_RECORDING_FALSE_START_RESET_MS
        ) {
          state.noiseFloor = Math.max(
            SMART_RECORDING_NOISE_FLOOR_DEFAULT,
            Math.min(startThreshold * 0.7, Math.max(state.noiseFloor, level)),
          );
          state.smoothedLevel = state.noiseFloor;
          state.consecutiveSpeechMs = 0;
          state.totalSpeechMs = 0;
          state.silenceMs = 0;
          state.utteranceMs = 0;
          state.hasSpeechStarted = false;
          state.lastSpeechAt = 0;
          setVoiceTrailingSilenceRemainingMs(null);
          setVoiceActivityState("listening");
          return;
        }

        if (
          state.silenceMs < SMART_RECORDING_SILENCE_CONFIRM_MS ||
          state.totalSpeechMs < SMART_RECORDING_MIN_SPEECH_MS
        ) {
          setVoiceTrailingSilenceRemainingMs(null);
          setVoiceActivityState("speech_detected");
          return;
        }

        const remainingSilenceMs = Math.max(
          0,
          SMART_RECORDING_TRAILING_SILENCE_MS - state.silenceMs,
        );
        setVoiceTrailingSilenceRemainingMs(remainingSilenceMs);

        if (
          state.silenceMs < SMART_RECORDING_TRAILING_SILENCE_MS &&
          state.utteranceMs < SMART_RECORDING_MAX_UTTERANCE_MS
        ) {
          return;
        }

        voiceStopPendingRef.current = true;
        setVoiceActivityState("processing");
        void stopVoiceRecording();
      }, SMART_RECORDING_CHECK_INTERVAL_MS);
    } catch {
      stopSmartRecordingTracking();
    }
  }

  function resetFlow(nextScenarioIndex = scenarioIndex) {
    const nextScenario = scenarios[nextScenarioIndex] ?? scenarios[0];
    setStepIndex(0);
    setAttemptInputMode("voice");
    setIsAttemptActive(false);
    setAttemptPhase("initial");
    setAttemptAnswer("");
    setSubmittedAttemptAnswer("");
    setSubmittedAttemptMode("text");
    setAttemptMessage(null);
    setAttemptPronunciationAssessment(null);
    setRetryInputMode(null);
    setRetryAnswer("");
    setSubmittedRetryAnswer("");
    setSubmittedRetryMode("text");
    setRetryMessage(null);
    setRetrySuccessful(false);
    setVoiceRecordingState(false);
    setVoiceProcessingState(false);
    setVoiceActivityState("idle");
    setVoiceTrailingSilenceRemainingMs(null);
    voiceStopPendingRef.current = false;
    stopSmartRecordingTracking();
    voiceTargetRef.current = null;

    if (!nextScenario) {
      setAttemptInputMode("voice");
    }
  }

  useEffect(() => {
    setScenarioIndex(0);
    resetFlow(0);
  }, [locale]);

  useEffect(() => {
    clearResultTimer();

    return () => {
      clearResultTimer();
      stopSmartRecordingTracking();
      mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      isVoiceRecordingRef.current = false;
      isVoiceProcessingRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!retrySuccessful) {
      return;
    }

    clearResultTimer();
    resultTimerRef.current = window.setTimeout(() => {
      setStepIndex(5);
    }, WELCOME_PROOF_LESSON_RESULT_DELAY_MS);

    return () => {
      clearResultTimer();
    };
  }, [retrySuccessful]);

  function getResolvedMode(mode: WelcomeProofLessonInputMode) {
    if (mode === "voice" && !voiceInputEnabled) {
      return "text";
    }

    return mode;
  }

  function validateAnswer(answer: string, scenarioItem: WelcomeProofLessonScenario) {
    if (!answer.trim()) {
      return scenarioItem.errors.answerRequired;
    }

    if (countWords(answer) < WELCOME_PROOF_LESSON_MIN_WORDS) {
      return scenarioItem.errors.answerTooShort;
    }

    return null;
  }

  function beginFirstAttempt(mode: WelcomeProofLessonInputMode) {
    if (isVoiceRecordingRef.current || isVoiceProcessingRef.current) {
      try {
        mediaRecorderRef.current?.stop();
      } catch {
        // Ignore invalid state transitions when switching modes mid-recording.
      }
      stopMediaTracks();
      setVoiceRecordingState(false);
      setVoiceProcessingState(false);
      setVoiceActivityState("idle");
      setVoiceTrailingSilenceRemainingMs(null);
      voiceStopPendingRef.current = false;
      voiceTargetRef.current = null;
    }

    const resolvedMode = getResolvedMode(mode);
    setIsAttemptActive(true);
    setAttemptInputMode(resolvedMode);
    setAttemptPhase("initial");
    setAttemptMessage(
      mode === "voice" && resolvedMode === "text"
        ? scenario.errors.micUnavailable
        : null,
    );
    setAttemptPronunciationAssessment(null);
    setAttemptAnswer("");
  }

  async function beginVoiceFirstAttempt() {
    const resolvedMode = getResolvedMode("voice");
    beginFirstAttempt("voice");
    if (resolvedMode === "voice") {
      await startVoiceRecording("attempt", "voice");
    }
  }

  function submitFirstAttempt() {
    const validationMessage = validateAnswer(attemptAnswer, scenario);
    if (validationMessage) {
      setAttemptMessage(validationMessage);
      return;
    }

    const trimmedAnswer = attemptAnswer.trim();
    const isRecommendedAttempt =
      attemptPhase === "recommended_repeat" ||
      matchesRecommendedFirstAttempt(trimmedAnswer, recommendedFirstAttempt);

    setAttemptMessage(null);
    setAttemptPronunciationAssessment(null);
    setIsAttemptActive(false);
    setSubmittedAttemptAnswer(trimmedAnswer);
    setSubmittedAttemptMode(attemptInputMode === "voice" ? "voice" : "text");
    if (isRecommendedAttempt) {
      setAttemptPhase("initial");
      setStepIndex(3);
      return;
    }

    setStepIndex(2);
  }

  function beginRetry(mode: WelcomeProofLessonInputMode) {
    if (isVoiceRecordingRef.current || isVoiceProcessingRef.current) {
      try {
        mediaRecorderRef.current?.stop();
      } catch {
        // Ignore invalid state transitions when switching modes mid-recording.
      }
      stopMediaTracks();
      setVoiceRecordingState(false);
      setVoiceProcessingState(false);
      setVoiceActivityState("idle");
      setVoiceTrailingSilenceRemainingMs(null);
      voiceStopPendingRef.current = false;
      voiceTargetRef.current = null;
    }

    const resolvedMode = getResolvedMode(mode);
    setRetryInputMode(resolvedMode);
    setRetryMessage(
      mode === "voice" && resolvedMode === "text"
        ? scenario.errors.micUnavailable
        : null,
    );
    setRetryAnswer("");
    setSubmittedRetryAnswer("");
    setSubmittedRetryMode("text");
    setRetrySuccessful(false);
  }

  function submitRetry() {
    const validationMessage = validateAnswer(retryAnswer, scenario);
    if (validationMessage) {
      setRetryMessage(validationMessage);
      return;
    }

    const trimmedAnswer = retryAnswer.trim();
    const successful =
      matchesAcceptedAnswer(trimmedAnswer, scenario.retry.acceptedAnswers) ||
      (normalizeAnswer(trimmedAnswer).includes("i'd like") &&
        normalizeAnswer(trimmedAnswer).includes("tea") &&
        normalizeAnswer(trimmedAnswer).includes("without") &&
        normalizeAnswer(trimmedAnswer).includes("milk"));

    setRetryMessage(successful ? null : scenario.errors.answerTooShort);
    setSubmittedRetryAnswer(trimmedAnswer);
    setSubmittedRetryMode(retryInputMode === "voice" ? "voice" : "text");
    setRetrySuccessful(successful);
  }

  function buildNextLesson() {
    writeGuestIntent({
      directions: scenario.guestIntentDirections,
      painPoint: scenario.id,
      lessonTone: "proof_first",
    });
    writeWelcomeProofLessonHandoff({
      locale,
      scenarioId: scenario.id,
      beforePhrase: feedback.userVersion,
      afterPhrase: feedback.improvedVersion,
      clarityStatusLabel,
      directions: scenario.guestIntentDirections,
      wins: scenario.result.points,
      createdAt: new Date().toISOString(),
    });
    navigate(WELCOME_PROOF_LESSON_NEXT_ROUTE);
  }

  function showAnotherExample() {
    const nextScenarioIndex = buildNextExampleScenarioIndex(scenarioIndex, scenarios);
    setScenarioIndex(nextScenarioIndex);
    resetFlow(nextScenarioIndex);
  }

  function beginRecommendedRepeat() {
    const nextInputMode = voiceInputEnabled ? "voice" : "text";
    setIsAttemptActive(true);
    setAttemptPhase("recommended_repeat");
    setAttemptInputMode(nextInputMode);
    setAttemptAnswer("");
    setAttemptPronunciationAssessment(null);
    setAttemptMessage(
      locale === "ru"
        ? `Теперь скажи именно эту фразу: ${recommendedFirstAttempt}`
        : `Now say this exact phrase: ${recommendedFirstAttempt}`,
    );
    setStepIndex(1);
  }

  function stopMediaTracks() {
    stopSmartRecordingTracking();
    mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaRecorderRef.current = null;
    mediaStreamRef.current = null;
  }

  async function startVoiceRecording(
    target: Exclude<WelcomeProofLessonVoiceTarget, null>,
    modeOverride?: WelcomeProofLessonInputMode | null,
  ) {
    if (isVoiceRecordingRef.current || isVoiceProcessingRef.current) {
      return;
    }

    const targetInputMode =
      modeOverride ?? (target === "attempt" ? attemptInputMode : retryInputMode);
    if (targetInputMode !== "voice") {
      return;
    }

    if (!voiceInputEnabled) {
      const fallbackMessage = scenario.errors.micUnavailable;
      if (target === "attempt") {
        setAttemptInputMode("text");
        setAttemptMessage(fallbackMessage);
      } else {
        setRetryInputMode("text");
        setRetryMessage(fallbackMessage);
      }
      return;
    }

    recordedChunksRef.current = [];
    voiceTargetRef.current = target;
    voiceStopPendingRef.current = false;
    resetSmartRecordingState();

    if (target === "attempt") {
      setIsAttemptActive(true);
      setAttemptMessage(null);
      setAttemptPronunciationAssessment(null);
      setAttemptAnswer("");
    } else {
      setRetryMessage(null);
      setRetryAnswer("");
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };
      mediaRecorder.start();
      setVoiceRecordingState(true);
      setVoiceActivityState("listening");
      setVoiceTrailingSilenceRemainingMs(null);
      startSmartRecordingTracking(target);
    } catch (error) {
      voiceTargetRef.current = null;
      stopSmartRecordingTracking();
      setVoiceActivityState("idle");
      setVoiceTrailingSilenceRemainingMs(null);
      const fallbackMessage =
        error instanceof Error && error.message ? error.message : scenario.errors.micUnavailable;
      if (target === "attempt") {
        setAttemptInputMode("text");
        setAttemptMessage(fallbackMessage);
      } else {
        setRetryInputMode("text");
        setRetryMessage(fallbackMessage);
      }
    }
  }

  async function stopVoiceRecording() {
    const mediaRecorder = mediaRecorderRef.current;
    const target = voiceTargetRef.current;
    if (!mediaRecorder || !target) {
      return;
    }

    if (isVoiceProcessingRef.current) {
      return;
    }
    voiceStopPendingRef.current = true;

    if (target === "attempt") {
      setAttemptMessage(null);
    } else {
      setRetryMessage(null);
    }
    setVoiceProcessingState(true);
    setVoiceActivityState("processing");
    setVoiceTrailingSilenceRemainingMs(null);
    stopSmartRecordingTracking();
    setVoiceRecordingState(false);

    const recordedBlob = await new Promise<Blob>((resolve, reject) => {
      const resolveBlob = () => {
        resolve(
          new Blob(recordedChunksRef.current, {
            type: mediaRecorder.mimeType || "audio/webm",
          }),
        );
      };

      if (mediaRecorder.state === "inactive") {
        resolveBlob();
        return;
      }

      mediaRecorder.onstop = () => {
        resolveBlob();
      };
      mediaRecorder.onerror = () => {
        reject(new Error(scenario.errors.recognitionFailed));
      };

      try {
        mediaRecorder.stop();
      } catch (error) {
        reject(error);
      }
    });

    stopMediaTracks();

    try {
      const response = await apiClient.transcribeSpeech(recordedBlob, "en");
      const transcript = response.transcript.trim();
      if (!transcript) {
        throw new Error(scenario.errors.recognitionFailed);
      }

      const validationMessage = validateAnswer(transcript, scenario);

      if (target === "attempt") {
        if (validationMessage) {
          setAttemptAnswer(transcript);
          setAttemptMessage(validationMessage);
          return;
        }

        const shouldScorePronunciation =
          attemptPhase === "recommended_repeat" ||
          matchesRecommendedFirstAttempt(transcript, recommendedFirstAttempt);

        if (!shouldScorePronunciation) {
          setAttemptAnswer(transcript);
          setAttemptMessage(null);
          setSubmittedAttemptAnswer(transcript);
          setSubmittedAttemptMode("voice");
          setAttemptPronunciationAssessment(null);
          setIsAttemptActive(false);
          setStepIndex(2);
          return;
        }

        const pronunciationTarget = recommendedFirstAttempt;
        let pronunciationAssessment: PronunciationAssessment | null = null;

        try {
          pronunciationAssessment = await apiClient.assessWelcomePronunciation({
            targetText: pronunciationTarget,
            audio: recordedBlob,
            language: "en",
          });
        } catch {
          pronunciationAssessment = null;
        }

        setAttemptAnswer(transcript);
        setAttemptMessage(null);
        setSubmittedAttemptAnswer(transcript);
        setSubmittedAttemptMode("voice");
        setAttemptPronunciationAssessment(pronunciationAssessment);
        setAttemptPhase("initial");
        setIsAttemptActive(false);
        setStepIndex(3);
      } else {
        if (validationMessage) {
          setRetryAnswer(transcript);
          setRetryMessage(validationMessage);
          setSubmittedRetryAnswer(transcript);
          setSubmittedRetryMode("voice");
          setRetrySuccessful(false);
          return;
        }

        const successful =
          matchesAcceptedAnswer(transcript, scenario.retry.acceptedAnswers) ||
          (normalizeAnswer(transcript).includes("i'd like") &&
            normalizeAnswer(transcript).includes("tea") &&
            normalizeAnswer(transcript).includes("without") &&
            normalizeAnswer(transcript).includes("milk"));

        setRetryAnswer(transcript);
        setRetryMessage(successful ? null : scenario.errors.recognitionFailed);
        setSubmittedRetryAnswer(transcript);
        setSubmittedRetryMode("voice");
        setRetrySuccessful(successful);
      }
    } catch (error) {
      const message =
        error instanceof Error && error.message ? error.message : scenario.errors.networkRetry;
      if (target === "attempt") {
        setAttemptMessage(message);
      } else {
        setRetryMessage(message);
      }
    } finally {
      voiceTargetRef.current = null;
      setVoiceProcessingState(false);
      setVoiceActivityState("idle");
      setVoiceTrailingSilenceRemainingMs(null);
      voiceStopPendingRef.current = false;
    }
  }

  return {
    attemptAnswer,
    attemptInputMode,
    attemptMessage,
    beginFirstAttempt,
    beginRetry,
    buildNextLesson,
    beginVoiceFirstAttempt,
    clarityStatusLabel,
    clarityHints,
    currentStep,
    feedback,
    goToClarity: () => {
      if (feedback.isAlreadyNatural) {
        setStepIndex(3);
        return;
      }

      beginRecommendedRepeat();
    },
    goToRetry: () => {
      setRetryInputMode(null);
      setRetryAnswer("");
      setSubmittedRetryAnswer("");
      setRetryMessage(null);
      setRetrySuccessful(false);
      setStepIndex(4);
    },
    isAttemptActive,
    retryAnswer,
    retryInputMode,
    retryMessage,
    retrySuccessful,
    scenario,
    setAttemptAnswer,
    setRetryAnswer,
    showAnotherExample,
    startVoiceRecording,
    startLesson: () => setStepIndex(1),
    stopVoiceRecording,
    stepIndex,
    submittedAttemptAnswer,
    submittedAttemptMode,
    submittedRetryAnswer,
    submittedRetryMode,
    submitFirstAttempt,
    submitRetry,
    totalSteps: WELCOME_PROOF_LESSON_STEPS.length,
    voiceActivityState,
    voiceTrailingSilenceRemainingMs,
    voiceInputEnabled,
    isVoiceProcessing,
    isVoiceRecording,
  };
}

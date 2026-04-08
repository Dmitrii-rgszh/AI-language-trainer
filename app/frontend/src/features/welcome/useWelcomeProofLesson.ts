import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import type { AppLocale } from "../../shared/i18n/locale";
import type { PronunciationAssessment } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
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

type WelcomeProofLessonStep =
  | "intro"
  | "situation"
  | "attempt"
  | "feedback"
  | "clarity"
  | "retry"
  | "result";

type ProofLessonResponseMode = "text" | "voice";
type WelcomeProofLessonVoiceTarget = "attempt" | "retry" | null;

const WELCOME_PROOF_LESSON_STEPS: WelcomeProofLessonStep[] = [
  "intro",
  "situation",
  "attempt",
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
  scenario: WelcomeProofLessonScenario,
  assessment: PronunciationAssessment | null,
): string[] {
  if (!assessment) {
    return scenario.clarity.hints;
  }

  const hints: string[] = [];
  for (const focus of assessment.focusAssessments) {
    if (focus.status === "stable") {
      continue;
    }
    if (focus.focus === "th") {
      hints.push(locale === "ru" ? "Сделай звук /th/ чётче" : "Make the /th/ sound clearer");
    } else if (focus.focus === "r-coloring") {
      hints.push(locale === "ru" ? "Чётче выдели звук /r/" : "Make the /r/ sound clearer");
    } else if (focus.focus === "word rhythm") {
      hints.push(locale === "ru" ? "Скажи фразу более слитно, без потери слов" : "Keep the phrase connected without dropping words");
    } else if (focus.focus === "word ending") {
      hints.push(locale === "ru" ? "Не съедай окончания слов" : "Do not swallow the word endings");
    }
  }

  for (const word of assessment.weakestWords) {
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
  const resultTimerRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const voiceTargetRef = useRef<WelcomeProofLessonVoiceTarget>(null);
  const scenario = scenarios[scenarioIndex] ?? scenarios[0];
  const currentStep = WELCOME_PROOF_LESSON_STEPS[stepIndex] ?? "intro";
  const voiceInputEnabled =
    typeof window !== "undefined" &&
    window.isSecureContext &&
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof MediaRecorder !== "undefined";

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
      attemptPronunciationAssessment && submittedAttemptMode === "voice"
        ? buildClarityStatusKeyFromScore(attemptPronunciationAssessment.score)
        : buildClarityStatusKey(submittedAttemptAnswer),
    [attemptPronunciationAssessment, submittedAttemptAnswer, submittedAttemptMode],
  );

  const clarityStatusLabel = scenario.clarity.statuses[clarityStatusKey];
  const clarityHints = useMemo(
    () =>
      submittedAttemptMode === "voice"
        ? buildPronunciationHints(locale, scenario, attemptPronunciationAssessment)
        : scenario.clarity.hints,
    [attemptPronunciationAssessment, locale, scenario, submittedAttemptMode],
  );

  function clearResultTimer() {
    if (resultTimerRef.current !== null) {
      window.clearTimeout(resultTimerRef.current);
      resultTimerRef.current = null;
    }
  }

  function resetFlow(nextScenarioIndex = scenarioIndex) {
    const nextScenario = scenarios[nextScenarioIndex] ?? scenarios[0];
    setStepIndex(0);
    setAttemptInputMode("voice");
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
    setIsVoiceRecording(false);
    setIsVoiceProcessing(false);
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
      mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  useEffect(() => {
    if (!retrySuccessful) {
      return;
    }

    clearResultTimer();
    resultTimerRef.current = window.setTimeout(() => {
      setStepIndex(6);
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
    const resolvedMode = getResolvedMode(mode);
    setAttemptInputMode(resolvedMode);
    setAttemptMessage(
      mode === "voice" && resolvedMode === "text"
        ? scenario.errors.micUnavailable
        : null,
    );
    setAttemptPronunciationAssessment(null);
    setAttemptAnswer("");
    setStepIndex(2);
  }

  function submitFirstAttempt() {
    const validationMessage = validateAnswer(attemptAnswer, scenario);
    if (validationMessage) {
      setAttemptMessage(validationMessage);
      return;
    }

    setAttemptMessage(null);
    setAttemptPronunciationAssessment(null);
    setSubmittedAttemptAnswer(attemptAnswer.trim());
    setSubmittedAttemptMode(attemptInputMode === "voice" ? "voice" : "text");
    setStepIndex(3);
  }

  function beginRetry(mode: WelcomeProofLessonInputMode) {
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
    navigate(WELCOME_PROOF_LESSON_NEXT_ROUTE);
  }

  function showAnotherExample() {
    const nextScenarioIndex = buildNextExampleScenarioIndex(scenarioIndex, scenarios);
    setScenarioIndex(nextScenarioIndex);
    resetFlow(nextScenarioIndex);
  }

  function stopMediaTracks() {
    mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaRecorderRef.current = null;
    mediaStreamRef.current = null;
  }

  async function startVoiceRecording(target: Exclude<WelcomeProofLessonVoiceTarget, null>) {
    if (isVoiceRecording || isVoiceProcessing) {
      return;
    }

    const targetInputMode = target === "attempt" ? attemptInputMode : retryInputMode;
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

    if (target === "attempt") {
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
      setIsVoiceRecording(true);
    } catch (error) {
      voiceTargetRef.current = null;
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

    if (target === "attempt") {
      setAttemptMessage(null);
    } else {
      setRetryMessage(null);
    }
    setIsVoiceProcessing(true);

    const recordedBlob = await new Promise<Blob>((resolve) => {
      mediaRecorder.onstop = () => {
        resolve(
          new Blob(recordedChunksRef.current, {
            type: mediaRecorder.mimeType || "audio/webm",
          }),
        );
      };
      mediaRecorder.stop();
    });

    stopMediaTracks();
    setIsVoiceRecording(false);

    try {
      const response = await apiClient.transcribeSpeech(recordedBlob);
      const transcript = response.transcript.trim();
      if (!transcript) {
        throw new Error(scenario.errors.recognitionFailed);
      }

      if (target === "attempt") {
        setAttemptAnswer(transcript);
        setAttemptMessage(null);
        setSubmittedAttemptAnswer(transcript);
        setSubmittedAttemptMode("voice");
        setStepIndex(3);
        void apiClient
          .assessPronunciation({
            targetText: transcript,
            audio: recordedBlob,
          })
          .then((assessment) => {
            setAttemptPronunciationAssessment(assessment);
          })
          .catch(() => undefined);
      } else {
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
      setIsVoiceProcessing(false);
    }
  }

  return {
    attemptAnswer,
    attemptInputMode,
    attemptMessage,
    beginFirstAttempt,
    beginRetry,
    buildNextLesson,
    clarityStatusLabel,
    clarityHints,
    currentStep,
    feedback,
    goToClarity: () => setStepIndex(4),
    goToRetry: () => {
      setRetryInputMode(null);
      setRetryAnswer("");
      setSubmittedRetryAnswer("");
      setRetryMessage(null);
      setRetrySuccessful(false);
      setStepIndex(5);
    },
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
    voiceInputEnabled,
    isVoiceProcessing,
    isVoiceRecording,
  };
}

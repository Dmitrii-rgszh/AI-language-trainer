import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { AppLocale } from "../../shared/i18n/locale";
import { routes } from "../../shared/constants/routes";
import { writeGuestIntent } from "./guest-intent";
import type {
  WelcomeProofLessonClarityStatusKey,
  WelcomeProofLessonInputMode,
  WelcomeProofLessonScenario,
} from "./welcomeProofLessonScenario";
import { welcomeProofLessonScenarios } from "./welcomeProofLessonScenario";

const WELCOME_PROOF_LESSON_NEXT_ROUTE = routes.onboarding;
const WELCOME_PROOF_LESSON_VOICE_ENABLED = false;
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
  const [retryInputMode, setRetryInputMode] =
    useState<WelcomeProofLessonInputMode | null>(null);
  const [retryAnswer, setRetryAnswer] = useState("");
  const [submittedRetryAnswer, setSubmittedRetryAnswer] = useState("");
  const [submittedRetryMode, setSubmittedRetryMode] =
    useState<ProofLessonResponseMode>("text");
  const [retryMessage, setRetryMessage] = useState<string | null>(null);
  const [retrySuccessful, setRetrySuccessful] = useState(false);
  const resultTimerRef = useRef<number | null>(null);
  const scenario = scenarios[scenarioIndex] ?? scenarios[0];
  const currentStep = WELCOME_PROOF_LESSON_STEPS[stepIndex] ?? "intro";

  const feedback = useMemo(() => {
    const userVersion =
      submittedAttemptAnswer.trim() || scenario.languageTargets.firstAttemptImproved;

    return {
      title: scenario.feedback.title,
      userVersion,
      improvedVersion: scenario.languageTargets.firstAttemptImproved,
      explanationPrimary: scenario.feedback.explanationPrimary,
      explanationSecondary: scenario.feedback.explanationSecondary,
    };
  }, [scenario, submittedAttemptAnswer]);

  const clarityStatusKey = useMemo(
    () => buildClarityStatusKey(submittedAttemptAnswer),
    [submittedAttemptAnswer],
  );

  const clarityStatusLabel = scenario.clarity.statuses[clarityStatusKey];

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
    setRetryInputMode(null);
    setRetryAnswer("");
    setSubmittedRetryAnswer("");
    setSubmittedRetryMode("text");
    setRetryMessage(null);
    setRetrySuccessful(false);

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
    if (mode === "voice" && !WELCOME_PROOF_LESSON_VOICE_ENABLED) {
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

  return {
    attemptAnswer,
    attemptInputMode,
    attemptMessage,
    beginFirstAttempt,
    beginRetry,
    buildNextLesson,
    clarityStatusLabel,
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
    startLesson: () => setStepIndex(1),
    stepIndex,
    submittedAttemptAnswer,
    submittedAttemptMode,
    submittedRetryAnswer,
    submittedRetryMode,
    submitFirstAttempt,
    submitRetry,
    totalSteps: WELCOME_PROOF_LESSON_STEPS.length,
    voiceInputEnabled: WELCOME_PROOF_LESSON_VOICE_ENABLED,
  };
}

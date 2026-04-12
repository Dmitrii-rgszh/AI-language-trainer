import type { AppLocale } from "../i18n/locale";
import type { GuestDirectionId } from "./guest-intent";

export type WelcomeProofLessonHandoff = {
  locale: AppLocale;
  scenarioId: string;
  beforePhrase: string;
  afterPhrase: string;
  clarityStatusLabel: string;
  directions: GuestDirectionId[];
  wins: string[];
  createdAt: string;
};

const WELCOME_PROOF_LESSON_HANDOFF_STORAGE_KEY =
  "ai-english-trainer:welcome-proof-handoff";

function normalizeDirections(value: unknown): GuestDirectionId[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is GuestDirectionId => typeof item === "string");
}

function normalizeWins(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 3);
}

export function readWelcomeProofLessonHandoff(): WelcomeProofLessonHandoff | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedValue = window.localStorage.getItem(
    WELCOME_PROOF_LESSON_HANDOFF_STORAGE_KEY,
  );
  if (!storedValue) {
    return null;
  }

  try {
    const parsedValue = JSON.parse(storedValue) as Partial<WelcomeProofLessonHandoff>;
    if (
      typeof parsedValue.locale !== "string" ||
      typeof parsedValue.scenarioId !== "string" ||
      typeof parsedValue.beforePhrase !== "string" ||
      typeof parsedValue.afterPhrase !== "string" ||
      typeof parsedValue.clarityStatusLabel !== "string"
    ) {
      return null;
    }

    return {
      locale: parsedValue.locale === "en" ? "en" : "ru",
      scenarioId: parsedValue.scenarioId,
      beforePhrase: parsedValue.beforePhrase.trim(),
      afterPhrase: parsedValue.afterPhrase.trim(),
      clarityStatusLabel: parsedValue.clarityStatusLabel.trim(),
      directions: normalizeDirections(parsedValue.directions),
      wins: normalizeWins(parsedValue.wins),
      createdAt:
        typeof parsedValue.createdAt === "string"
          ? parsedValue.createdAt
          : new Date().toISOString(),
    };
  } catch {
    return null;
  }
}

export function writeWelcomeProofLessonHandoff(
  handoff: WelcomeProofLessonHandoff,
) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(
    WELCOME_PROOF_LESSON_HANDOFF_STORAGE_KEY,
    JSON.stringify({
      ...handoff,
      wins: handoff.wins.slice(0, 3),
    }),
  );
}

export function clearWelcomeProofLessonHandoff() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(WELCOME_PROOF_LESSON_HANDOFF_STORAGE_KEY);
}

import { useEffect, useState } from "react";
import { apiClient } from "../../shared/api/client";
import type { AppLocale } from "../../shared/i18n/locale";
import type { ProviderStatus } from "../../shared/types/app-data";
import {
  getWelcomeAiTutorIntroVariants,
  getWelcomeProofLessonCoachPrompt,
} from "./welcomeAiTutorPrompts";

const WELCOME_PRESENCE_VIDEO_REVISION = "presence-01-v2-forced";
const WELCOME_TUTOR_PRESET_REVISION = "welcome-presets-v6-presence-01-forced";
const WELCOME_TUTOR_CLARITY_PRESET_REVISION = "welcome-presets-v7-stable-coach";
const PROOF_LESSON_BACKGROUND_WARMUP_DELAY_MS = 120;

type WelcomeProofLessonRuntimePhase = "preparing" | "ready" | "error";

export type WelcomeProofLessonRuntime = {
  phase: WelcomeProofLessonRuntimePhase;
  canStart: boolean;
  title: string;
  description: string;
  detail: string | null;
};

function getResultCoachMessage(locale: AppLocale) {
  return locale === "ru"
    ? "Ты уже почувствовал, как Verba превращает живую фразу в понятный навык. Теперь сохраним этот старт в твоём профиле и соберём личный трек."
    : "You already felt how Verba turns one live phrase into a usable skill. Next we save this start in your profile and build a personal track around it.";
}

function buildPreparingState(locale: AppLocale): WelcomeProofLessonRuntime {
  return locale === "ru"
    ? {
        phase: "preparing",
        canStart: false,
        title: "Лиза подготавливает живой урок",
        description:
          "Проверяем lip-sync, голос, распознавание речи и анализ произношения, чтобы мини-урок стартовал без деградации и скрытых упрощений.",
        detail: null,
      }
    : {
        phase: "preparing",
        canStart: false,
        title: "Liza is preparing the live lesson",
        description:
          "We are checking lip sync, voice, speech recognition, and pronunciation analysis so the mini-lesson starts without degraded paths or hidden simplifications.",
        detail: null,
      };
}

function buildReadyState(locale: AppLocale): WelcomeProofLessonRuntime {
  return locale === "ru"
    ? {
        phase: "ready",
        canStart: true,
        title: "Живой режим готов",
        description:
          "Lip-sync, голос Лизы и speech-analysis уже прогреты. Можно запускать пробный урок как цельный live-опыт.",
        detail: null,
      }
    : {
        phase: "ready",
        canStart: true,
        title: "Live mode is ready",
        description:
          "Lip sync, Liza’s voice, and speech analysis are warmed up. You can start the proof lesson as one cohesive live experience.",
        detail: null,
      };
}

function buildErrorState(
  locale: AppLocale,
  detail: string,
): WelcomeProofLessonRuntime {
  return locale === "ru"
    ? {
        phase: "error",
        canStart: false,
        title: "Живой урок ещё не готов",
        description:
          "Один из обязательных speech-компонентов не поднялся. Давай сначала доведём живой runtime до готовности, а потом уже начнём урок.",
        detail,
      }
    : {
        phase: "error",
        canStart: false,
        title: "The live lesson is not ready yet",
        description:
          "One of the required speech components is not ready. Let us bring the live runtime to full readiness first and only then start the lesson.",
        detail,
      };
}

function ensureRequiredProviders(
  locale: AppLocale,
  providers: ProviderStatus[],
) {
  const requiredTypes = ["tts", "stt", "scoring"] as const;
  const unavailableProviders = requiredTypes
    .map((type) => providers.find((provider) => provider.type === type))
    .filter((provider) => !provider || provider.status !== "ready");

  if (unavailableProviders.length === 0) {
    return;
  }

  const readableTypes = unavailableProviders.map((provider) => {
    const type = provider?.type ?? "unknown";
    if (locale === "ru") {
      switch (type) {
        case "tts":
          return "голос Лизы";
        case "stt":
          return "распознавание речи";
        case "scoring":
          return "анализ произношения";
        default:
          return "speech pipeline";
      }
    }

    switch (type) {
      case "tts":
        return "Liza voice";
      case "stt":
        return "speech recognition";
      case "scoring":
        return "pronunciation analysis";
      default:
        return "speech pipeline";
    }
  });

  throw new Error(
    locale === "ru"
      ? `Не готовы: ${readableTypes.join(", ")}.`
      : `Not ready: ${readableTypes.join(", ")}.`,
  );
}

async function warmProofLessonRuntime(locale: AppLocale) {
  const introVariants = getWelcomeAiTutorIntroVariants(locale);
  const [welcomeTutorStatus, providers] = await Promise.all([
    apiClient.getWelcomeTutorStatus(),
    apiClient.getProviders(),
  ]);

  if (!welcomeTutorStatus.available || welcomeTutorStatus.mode !== "musetalk") {
    throw new Error(welcomeTutorStatus.details);
  }

  ensureRequiredProviders(locale, providers);

  await Promise.all([
    apiClient.preloadLiveAvatarPresenceVideo(
      "verba_tutor",
      WELCOME_PRESENCE_VIDEO_REVISION,
    ),
    ...introVariants.map((_, variant) =>
      apiClient.prefetchWelcomeTutorPresetClip({
        locale: locale === "ru" ? "ru" : "en",
        kind: "intro",
        variant,
        revision: WELCOME_TUTOR_PRESET_REVISION,
      }),
    ),
    apiClient.prefetchWelcomeTutorPresetClip({
      locale: locale === "ru" ? "ru" : "en",
      kind: "replay",
      variant: 0,
      revision: WELCOME_TUTOR_PRESET_REVISION,
    }),
  ]);
}

async function warmProofLessonBackgroundAssets(locale: AppLocale) {
  const resultCoachMessage = getResultCoachMessage(locale);

  await Promise.allSettled([
    apiClient.prefetchWelcomeTutorClip({
      text: getWelcomeProofLessonCoachPrompt(locale, "feedback"),
      language: locale === "ru" ? "ru" : "en",
      avatarKey: "verba_tutor",
      cacheSignature: `${locale}:proof:feedback`,
    }),
    apiClient.prefetchWelcomeTutorClip({
      text: getWelcomeProofLessonCoachPrompt(locale, "retry"),
      language: locale === "ru" ? "ru" : "en",
      avatarKey: "verba_tutor",
      cacheSignature: `${locale}:proof:retry`,
    }),
    apiClient.prefetchWelcomeTutorClip({
      text: resultCoachMessage,
      language: locale === "ru" ? "ru" : "en",
      avatarKey: "verba_tutor",
      cacheSignature: `${locale}:proof:result`,
    }),
    apiClient.prefetchWelcomeTutorPresetClip({
      locale: locale === "ru" ? "ru" : "en",
      kind: "clarity_intro",
      variant: 0,
      revision: WELCOME_TUTOR_CLARITY_PRESET_REVISION,
    }),
    apiClient.prefetchWelcomeTutorPresetClip({
      locale: locale === "ru" ? "ru" : "en",
      kind: "clarity_model",
      variant: 0,
      revision: WELCOME_TUTOR_CLARITY_PRESET_REVISION,
    }),
  ]);
}

export function useWelcomeProofLessonRuntime(
  locale: AppLocale,
  enabled: boolean,
) {
  const [retryNonce, setRetryNonce] = useState(0);
  const [runtime, setRuntime] = useState<WelcomeProofLessonRuntime>(() =>
    buildPreparingState(locale),
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;
    let backgroundWarmupTimeoutId: number | null = null;
    setRuntime(buildPreparingState(locale));

    void warmProofLessonRuntime(locale)
      .then(() => {
        if (!cancelled) {
          setRuntime(buildReadyState(locale));
        }

        backgroundWarmupTimeoutId = window.setTimeout(() => {
          if (!cancelled) {
            void warmProofLessonBackgroundAssets(locale);
          }
        }, PROOF_LESSON_BACKGROUND_WARMUP_DELAY_MS);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        const detail =
          error instanceof Error && error.message
            ? error.message
            : locale === "ru"
              ? "Не удалось прогреть живой speech-runtime."
              : "Could not warm up the live speech runtime.";
        setRuntime(buildErrorState(locale, detail));
      });

    return () => {
      cancelled = true;
      if (backgroundWarmupTimeoutId !== null) {
        window.clearTimeout(backgroundWarmupTimeoutId);
      }
    };
  }, [enabled, locale, retryNonce]);

  const retry = () => {
    setRetryNonce((current) => current + 1);
  };

  return {
    runtime,
    retry,
  };
}

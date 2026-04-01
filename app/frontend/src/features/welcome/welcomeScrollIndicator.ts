import type { AppLocale } from "../../shared/i18n/locale";
import type { ConvergingPathsScrollIndicatorTimings } from "../../shared/ui/ConvergingPathsScrollIndicator";

export const welcomeScrollIndicatorMessages: Record<AppLocale, readonly string[]> = {
  ru: [
    "Ниже — как Verba собирает обучение в одну систему.",
    "Ниже — как устроена Verba",
    "Прокрутите, чтобы увидеть систему",
    "Следующий слой — ниже",
    "Посмотреть, как это работает",
  ],
  en: [
    "Below is how Verba brings learning into one system.",
    "Below is how Verba works",
    "Scroll to see the system",
    "The next layer is below",
    "See how it works",
  ],
};

export const welcomeScrollIndicatorTimings: ConvergingPathsScrollIndicatorTimings = {
  separationHoldMs: 760,
  convergenceMs: 860,
  directionBirthMs: 460,
  settleMs: 820,
};

export const welcomeScrollIndicatorConfig = {
  activeMessageIndex: 0,
  color: "rgba(39, 55, 69, 0.76)",
  height: 54,
  intensity: 1.02,
  opacity: 0.98,
  timings: welcomeScrollIndicatorTimings,
  width: 104,
} as const;

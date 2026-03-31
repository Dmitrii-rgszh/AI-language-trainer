import { useAppStore } from "../store/app-store";
import {
  formatAdaptiveHeadline,
  formatAdaptiveSummary,
  formatDate,
  formatDateTime,
  formatDays,
  formatRecommendationGoal,
  formatRoadmapSummary,
  translateList,
  translateText,
  translateToken,
} from "./locale";

export function useLocale() {
  const locale = useAppStore((state) => state.locale);
  const setLocale = useAppStore((state) => state.setLocale);

  return {
    locale,
    setLocale,
    tr: (value: string) => translateText(locale, value),
    tt: (value: string) => translateToken(locale, value),
    tl: (values: string[]) => translateList(locale, values),
    formatAdaptiveHeadline: (name: string, focusArea: string) => formatAdaptiveHeadline(locale, name, focusArea),
    formatAdaptiveSummary: (options: Parameters<typeof formatAdaptiveSummary>[1]) => formatAdaptiveSummary(locale, options),
    formatRecommendationGoal: (options: Parameters<typeof formatRecommendationGoal>[1]) =>
      formatRecommendationGoal(locale, options),
    formatRoadmapSummary: (options: Parameters<typeof formatRoadmapSummary>[1]) => formatRoadmapSummary(locale, options),
    formatDate: (value: string) => formatDate(locale, value),
    formatDateTime: (value: string) => formatDateTime(locale, value),
    formatDays: (value: number) => formatDays(locale, value),
  };
}

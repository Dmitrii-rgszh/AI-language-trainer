import { useAppStore } from "../store/app-store";
import { formatDate, formatDateTime, formatDays, translateList, translateText, translateToken } from "./locale";

export function useLocale() {
  const locale = useAppStore((state) => state.locale);
  const setLocale = useAppStore((state) => state.setLocale);

  return {
    locale,
    setLocale,
    tr: (value: string) => translateText(locale, value),
    tt: (value: string) => translateToken(locale, value),
    tl: (values: string[]) => translateList(locale, values),
    formatDate: (value: string) => formatDate(locale, value),
    formatDateTime: (value: string) => formatDateTime(locale, value),
    formatDays: (value: number) => formatDays(locale, value),
  };
}

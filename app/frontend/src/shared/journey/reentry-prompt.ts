const JOURNEY_REENTRY_DISMISSED_KEY = "journey-reentry-dismissed-key";

export function readDismissedJourneyReentryKey() {
  try {
    return window.localStorage.getItem(JOURNEY_REENTRY_DISMISSED_KEY);
  } catch {
    return null;
  }
}

export function writeDismissedJourneyReentryKey(key: string) {
  try {
    window.localStorage.setItem(JOURNEY_REENTRY_DISMISSED_KEY, key);
  } catch {
    // noop
  }
}

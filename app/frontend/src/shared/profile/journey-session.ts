const JOURNEY_SESSION_STORAGE_KEY = "ai-english-trainer:journey-session-id";

export function readStoredJourneySessionId() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(JOURNEY_SESSION_STORAGE_KEY);
}

export function writeStoredJourneySessionId(sessionId: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(JOURNEY_SESSION_STORAGE_KEY, sessionId);
}

export function clearStoredJourneySessionId() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(JOURNEY_SESSION_STORAGE_KEY);
}

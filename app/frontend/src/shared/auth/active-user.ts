const ACTIVE_USER_STORAGE_KEY = "ai-english-trainer:active-user-id";

export function readStoredActiveUserId() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(ACTIVE_USER_STORAGE_KEY);
}

export function writeStoredActiveUserId(userId: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(ACTIVE_USER_STORAGE_KEY, userId);
}

export function clearStoredActiveUserId() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(ACTIVE_USER_STORAGE_KEY);
}

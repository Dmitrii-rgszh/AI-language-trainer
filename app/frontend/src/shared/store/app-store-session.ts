import type { UserAccount } from "../../entities/account/model";
import type { UserOnboarding } from "../../entities/onboarding/model";
import type { UserProfile } from "../../entities/user/model";
import { ApiError, apiClient } from "../api/client";
import {
  clearStoredActiveUserId,
  readStoredActiveUserId,
  writeStoredActiveUserId,
} from "../auth/active-user";
import { normalizeLocale, readStoredLocale, writeStoredLocale } from "../i18n/locale";
import { createOnboardingRequiredState } from "./app-store.state";
import type { AppState, AppStoreGet, AppStoreSet } from "./app-store.types";

type SessionActionKeys =
  | "setLocale"
  | "bootstrap"
  | "signIn"
  | "completeOnboarding"
  | "saveCurrentUser"
  | "saveProfile"
  | "saveProviderPreference";

type StaticCatalogData = Pick<
  AppState,
  | "grammarTopics"
  | "speakingScenarios"
  | "pronunciationDrills"
  | "writingTask"
  | "professionTracks"
  | "providers"
>;

async function loadStaticCatalogData(): Promise<StaticCatalogData> {
  const [grammarTopics, speakingScenarios, pronunciationDrills, writingTask, professionTracks, providers] =
    await Promise.all([
      apiClient.getGrammarTopics(),
      apiClient.getSpeakingScenarios(),
      apiClient.getPronunciationDrills(),
      apiClient.getWritingTask(),
      apiClient.getProfessionTracks(),
      apiClient.getProviders(),
    ]);

  return {
    grammarTopics,
    speakingScenarios,
    pronunciationDrills,
    writingTask,
    professionTracks,
    providers,
  };
}

async function loadCurrentUser(): Promise<UserAccount | null> {
  try {
    return await apiClient.getCurrentUser();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      clearStoredActiveUserId();
      return null;
    }

    throw error;
  }
}

async function loadCurrentOnboarding(): Promise<UserOnboarding | null> {
  try {
    return await apiClient.getCurrentOnboarding();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function loadCurrentProfile(): Promise<UserProfile | null> {
  try {
    return await apiClient.getProfile();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

async function loadBootstrapSession(get: AppStoreGet): Promise<Partial<AppState> | null> {
  if (!readStoredActiveUserId()) {
    return null;
  }

  const currentUser = await loadCurrentUser();
  if (!currentUser) {
    return null;
  }

  const currentOnboarding = await loadCurrentOnboarding();
  const profile = await loadCurrentProfile();
  if (!profile) {
    return createOnboardingRequiredState({
      currentUser,
      currentOnboarding,
    });
  }

  const [dashboard, mistakes, progress, diagnosticRoadmap, providerPreferences] = await Promise.all([
    apiClient.getDashboardData(),
    apiClient.getMistakes(),
    apiClient.getProgress(),
    apiClient.getDiagnosticRoadmap(),
    apiClient.getProviderPreferences(),
  ]);

  const storedLocale = readStoredLocale();
  const nextLocale = storedLocale ?? normalizeLocale(profile.preferredUiLanguage, get().locale);

  if (!storedLocale) {
    writeStoredLocale(nextLocale);
  }

  return {
    locale: nextLocale,
    isBootstrapping: false,
    bootstrapError: null,
    needsOnboarding: false,
    currentUser,
    currentOnboarding,
    profile,
    dashboard,
    lesson: null,
    lastLessonResult: null,
    activeLessonRunId: null,
    selectedBlockIndex: 0,
    blockResponses: {},
    blockScores: {},
    listeningTranscriptReveals: {},
    mistakes,
    progress,
    diagnosticRoadmap,
    providerPreferences,
  };
}

export function createSessionActions(
  set: AppStoreSet,
  get: AppStoreGet,
): Pick<AppState, SessionActionKeys> {
  return {
    setLocale: (locale) => {
      const normalizedLocale = normalizeLocale(locale);
      writeStoredLocale(normalizedLocale);

      set((state) => ({
        locale: normalizedLocale,
        profile: state.profile ? { ...state.profile, preferredUiLanguage: normalizedLocale } : state.profile,
        dashboard: state.dashboard
          ? {
              ...state.dashboard,
              profile: { ...state.dashboard.profile, preferredUiLanguage: normalizedLocale },
            }
          : state.dashboard,
      }));
    },
    bootstrap: async () => {
      if (get().isBootstrapping) {
        return;
      }

      set({ isBootstrapping: true, bootstrapError: null });

      try {
        set(await loadStaticCatalogData());

        const sessionData = await loadBootstrapSession(get);
        if (!sessionData) {
          set(createOnboardingRequiredState());
          return;
        }

        set(sessionData);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to bootstrap app data";
        set({ isBootstrapping: false, bootstrapError: message });
      }
    },
    signIn: async (payload) => {
      const restoredUser = await apiClient.signIn({
        login: payload.login.trim(),
        email: payload.email.trim(),
      });

      writeStoredActiveUserId(restoredUser.id);
      await get().bootstrap();

      return {
        needsOnboarding: get().needsOnboarding,
      };
    },
    completeOnboarding: async (payload) => {
      const response = await apiClient.completeOnboarding(payload);
      writeStoredActiveUserId(response.user.id);

      const nextLocale = normalizeLocale(response.profile.preferredUiLanguage, get().locale);
      writeStoredLocale(nextLocale);

      set({
        locale: nextLocale,
        bootstrapError: null,
        needsOnboarding: false,
        currentUser: response.user,
        currentOnboarding: response.onboarding,
        profile: response.profile,
      });

      await get().bootstrap();
    },
    saveCurrentUser: async (payload) => {
      const savedUser = await apiClient.saveCurrentUser(payload);
      set({ currentUser: savedUser });
    },
    saveProfile: async (profile) => {
      const savedProfile = await apiClient.saveProfile(profile);
      const nextLocale = normalizeLocale(savedProfile.preferredUiLanguage, get().locale);
      writeStoredLocale(nextLocale);

      set((state) => ({
        locale: nextLocale,
        needsOnboarding: false,
        bootstrapError: null,
        profile: savedProfile,
        dashboard: state.dashboard ? { ...state.dashboard, profile: savedProfile } : state.dashboard,
      }));

      await get().bootstrap();
    },
    saveProviderPreference: async (providerType, enabled) => {
      const currentStatus = get().providers.find((provider) => provider.type === providerType);
      if (!currentStatus) {
        return;
      }

      const savedPreference = await apiClient.saveProviderPreference(providerType, {
        selectedProvider: currentStatus.key,
        enabled,
        settings: {},
      });

      set((state) => ({
        providerPreferences: [
          ...state.providerPreferences.filter((preference) => preference.providerType !== providerType),
          savedPreference,
        ],
      }));
    },
  };
}

import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { defaultUserAccountDraft, type UserAccountDraft } from "../../entities/account/model";
import type { OnboardingAnswers, UserProfile } from "../../entities/user/model";
import { ApiError, apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import {
  buildProfileDraft,
  cloneAnswers,
  diagnosticReadinessOptions,
  fallbackProfessionTracks,
  goalOptions,
  inferLearnerPersona,
  preferredModeOptions,
  skillFocusOptions,
  toggleValue,
  type OnboardingOption,
} from "../../shared/profile/profile-form-config";
import { applyGuestIntentToProfile, consumeGuestIntent } from "../../shared/profile/guest-intent";
import {
  clearStoredJourneySessionId,
  readStoredJourneySessionId,
  writeStoredJourneySessionId,
} from "../../shared/profile/journey-session";
import {
  clearWelcomeProofLessonHandoff,
  readWelcomeProofLessonHandoff,
} from "../../shared/profile/welcome-proof-handoff";
import { useAppStore } from "../../shared/store/app-store";
import type { ProfessionTrackCard } from "../../shared/types/app-data";
import { useAccountAvailability } from "./useAccountAvailability";

type ToggleAnswerField =
  | "secondaryGoals"
  | "activeSkillFocus"
  | "studyPreferences"
  | "supportNeeds"
  | "interestTopics";

type OnboardingStepDefinition = {
  description: string;
  helper: string;
  ready: boolean;
  title: string;
};

export function useOnboardingFlow() {
  const { locale, setLocale, tr } = useLocale();
  const currentUser = useAppStore((state) => state.currentUser);
  const profile = useAppStore((state) => state.profile);
  const professionTracks = useAppStore((state) => state.professionTracks);
  const completeOnboarding = useAppStore((state) => state.completeOnboarding);
  const navigate = useNavigate();
  const [account, setAccount] = useState<UserAccountDraft>(defaultUserAccountDraft);
  const [form, setForm] = useState<UserProfile>(() => buildProfileDraft(profile));
  const [step, setStep] = useState(0);
  const [isSaving, setIsSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [welcomeHandoff] = useState(() => readWelcomeProofLessonHandoff());
  const [journeySessionId, setJourneySessionId] = useState<string | null>(() => readStoredJourneySessionId());
  const [isHydratingSession, setIsHydratingSession] = useState(true);
  const draftSaveTimeoutRef = useRef<number | null>(null);
  const { loginCheck, emailCheck, emailIsValid } = useAccountAvailability(account);

  useEffect(() => {
    setAccount(
      currentUser
        ? {
            login: currentUser.login,
            email: currentUser.email,
          }
        : defaultUserAccountDraft,
    );
  }, [currentUser]);

  useEffect(() => {
    setForm(buildProfileDraft(profile));
    setStep(0);
  }, [profile]);

  useEffect(() => {
    const guestIntent = consumeGuestIntent();
    if (!guestIntent || guestIntent.directions.length === 0) {
      return;
    }

    setForm((current) => applyGuestIntentToProfile(current, guestIntent.directions));
  }, []);

  useEffect(() => {
    setForm((current) =>
      current.preferredUiLanguage === locale ? current : { ...current, preferredUiLanguage: locale },
    );
  }, [locale]);

  useEffect(() => {
    setSubmitError(null);
  }, [account.email, account.login]);

  useEffect(() => {
    let cancelled = false;

    async function hydrateSession() {
      setIsHydratingSession(true);
      try {
        let sessionId = readStoredJourneySessionId();
        let session = null;

        if (sessionId) {
          try {
            session = await apiClient.getOnboardingJourneySession(sessionId);
          } catch {
            session = null;
          }
        }

        if (!session) {
          session = await apiClient.startOnboardingJourneySession({
            source: welcomeHandoff ? "proof_lesson" : "direct_onboarding",
            proofLessonHandoff: welcomeHandoff ?? undefined,
          });
          sessionId = session.id;
          writeStoredJourneySessionId(sessionId);
        }

        if (cancelled) {
          return;
        }

        setJourneySessionId(sessionId);
        if (session.accountDraft.login || session.accountDraft.email) {
          setAccount(session.accountDraft);
        }
        if (session.profileDraft) {
          setForm(buildProfileDraft(session.profileDraft));
        }
        setStep(Math.max(0, session.currentStep ?? 0));
      } finally {
        if (!cancelled) {
          setIsHydratingSession(false);
        }
      }
    }

    void hydrateSession();

    return () => {
      cancelled = true;
    };
  }, [welcomeHandoff]);

  const tracks: ProfessionTrackCard[] =
    professionTracks.length > 0 ? professionTracks : fallbackProfessionTracks;
  const activeTrack = useMemo(
    () => tracks.find((track) => track.domain === form.professionTrack) ?? tracks[0],
    [form.professionTrack, tracks],
  );

  const loginStatusAllowsContinue =
    loginCheck.status === "available" || loginCheck.status === "existing_account";
  const accountReady =
    account.login.trim().length >= 3 && emailIsValid && loginStatusAllowsContinue;
  const basicsReady = form.name.trim().length > 0;
  const goalsReady =
    form.onboardingAnswers.primaryGoal.trim().length > 0 &&
    form.professionTrack.trim().length > 0 &&
    form.onboardingAnswers.preferredMode.trim().length > 0 &&
    form.onboardingAnswers.diagnosticReadiness.trim().length > 0;
  const rhythmReady =
    form.lessonDuration >= 10 &&
    form.lessonDuration <= 60 &&
    form.onboardingAnswers.activeSkillFocus.length > 0;

  const steps: OnboardingStepDefinition[] = useMemo(
    () => [
      {
        title:
          locale === "ru"
            ? welcomeHandoff
              ? "Сохраним твой старт"
              : "Аккаунт"
            : welcomeHandoff
              ? "Save your start"
              : "Account",
        description:
          locale === "ru"
            ? welcomeHandoff
              ? "Создай логин и email, чтобы сохранить результат пробного урока и продолжить уже в личном пространстве."
              : "Выбери логин и email, чтобы мы сохранили твой старт под правильным профилем."
            : welcomeHandoff
              ? "Create your login and email so we can save the proof-lesson result and continue inside your personal learning space."
              : "Choose a login and email so we can save your start under the right learner profile.",
        ready: accountReady,
        helper:
          locale === "ru"
            ? "Сначала нужен корректный логин и email."
            : "A valid login and email come first.",
      },
      {
        title: tr("Basics"),
        description: tr(
          "Set the learner name, languages, and current level so explanations and pacing start in the right place.",
        ),
        ready: basicsReady,
        helper: tr("Add a learner name to continue."),
      },
      {
        title: tr("Goal"),
        description: tr("Choose the main goal, the first content lane, the preferred mode, and diagnostic readiness."),
        ready: goalsReady,
        helper: tr("Pick the main goal, mode, and the first lane."),
      },
      {
        title: tr("Rhythm"),
        description: tr("Set the time budget and the first skills that should shape the daily loop."),
        ready: rhythmReady,
        helper: tr("Keep lesson duration between 10 and 60 minutes."),
      },
      {
        title: tr("Review"),
        description: tr("Check the summary before we open the dashboard and the first guided daily loop."),
        ready: accountReady && basicsReady && goalsReady && rhythmReady,
        helper: tr("Review the setup and create the workspace."),
      },
    ],
    [accountReady, basicsReady, goalsReady, locale, rhythmReady, tr, welcomeHandoff],
  );

  useEffect(() => {
    setStep((current) => Math.min(current, steps.length - 1));
  }, [steps.length]);

  useEffect(() => {
    if (!journeySessionId || isHydratingSession) {
      return;
    }

    if (draftSaveTimeoutRef.current !== null) {
      window.clearTimeout(draftSaveTimeoutRef.current);
    }

    draftSaveTimeoutRef.current = window.setTimeout(() => {
      void apiClient.saveOnboardingJourneyDraft(journeySessionId, {
        accountDraft: {
          login: account.login.trim(),
          email: account.email.trim(),
        },
        profileDraft: {
          ...form,
          onboardingAnswers: cloneAnswers(form.onboardingAnswers),
        },
        currentStep: step,
      }).catch(() => undefined);
    }, 320);

    return () => {
      if (draftSaveTimeoutRef.current !== null) {
        window.clearTimeout(draftSaveTimeoutRef.current);
        draftSaveTimeoutRef.current = null;
      }
    };
  }, [account, form, step, journeySessionId, isHydratingSession]);

  const activeStep = steps[step];
  const allCoreStepsReady = steps.slice(0, -1).every((item) => item.ready);

  const activeStepHelper = useMemo(() => {
    if (step !== 0) {
      return activeStep.helper;
    }

    if (loginCheck.status === "taken") {
      return tr("This name is already in use, but you can tap one of the free options below.");
    }

    if (loginCheck.status === "existing_account") {
      return tr("This login and email already match an existing account. You can continue.");
    }

    if (emailCheck.status === "invalid") {
      return tr("Add a valid email so we can create the learner workspace.");
    }

    if (loginCheck.status === "checking") {
      return tr("Checking the login against the current user base...");
    }

    return activeStep.helper;
  }, [activeStep.helper, emailCheck.status, loginCheck.status, step, tr]);

  const updateField = <K extends keyof UserProfile>(field: K, value: UserProfile[K]) =>
    setForm((current) => ({ ...current, [field]: value }));

  const updateAnswer = <K extends keyof OnboardingAnswers>(field: K, value: OnboardingAnswers[K]) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: { ...current.onboardingAnswers, [field]: value },
    }));

  const updateLearningContext = (value: string) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: {
        ...current.onboardingAnswers,
        learningContext: value,
        learnerPersona: inferLearnerPersona(current.onboardingAnswers.ageGroup, value),
      },
    }));

  const toggleAnswer = (field: ToggleAnswerField, value: string) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: {
        ...current.onboardingAnswers,
        [field]: toggleValue(current.onboardingAnswers[field], value),
      },
    }));

  const handleLocaleChange = (nextLocale: "ru" | "en") => {
    setLocale(nextLocale);
    updateField("preferredUiLanguage", nextLocale);
  };

  const goBack = () => setStep((current) => Math.max(0, current - 1));
  const goNext = () => setStep((current) => Math.min(steps.length - 1, current + 1));

  const submit = async () => {
    if (!allCoreStepsReady) {
      return;
    }

    setIsSaving(true);
    setSubmitError(null);
    try {
      await completeOnboarding({
        login: account.login.trim(),
        email: account.email.trim(),
        sessionId: journeySessionId,
        profile: {
          ...form,
          name: form.name.trim(),
          onboardingAnswers: cloneAnswers(form.onboardingAnswers),
        },
      });
      clearWelcomeProofLessonHandoff();
      clearStoredJourneySessionId();
      navigate(routes.dashboard, {
        state: {
          routeEntryReason:
            locale === "ru"
              ? "Лиза уже сохранила твой старт, цель и ритм обучения, поэтому dashboard открывается как точка входа в первый личный маршрут, а не как общий список экранов."
              : "Liza has already saved your start, goal, and learning rhythm, so the dashboard opens as the entry into your first personal route instead of a generic list of screens.",
          routeEntrySource: "onboarding_completion",
          routeEntryFollowUpLabel: locale === "ru" ? "первый daily route" : "first daily route",
          routeEntryStageLabel: locale === "ru" ? "Первый маршрут готов" : "First route ready",
          skipRouteEntryOrchestrationOnce: true,
        },
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setSubmitError(tr("This login or email is already linked to another account."));
      } else {
        setSubmitError(tr("Could not complete onboarding right now."));
      }
    } finally {
      setIsSaving(false);
    }
  };

  const helperOptionGroups: {
    diagnosticReadinessOptions: OnboardingOption[];
    preferredModeOptions: OnboardingOption[];
  } = {
    diagnosticReadinessOptions,
    preferredModeOptions,
  };

  return {
    account,
    activeStep,
    activeStepHelper,
    activeTrack,
    allCoreStepsReady,
    emailCheck,
    form,
    goBack,
    goNext,
    handleLocaleChange,
    helperOptionGroups,
    isHydratingSession,
    isSaving,
    journeySessionId,
    loginCheck,
    setAccount,
    setStep,
    step,
    steps,
    submit,
    submitError,
    tracks,
    updateAnswer,
    updateField,
    updateLearningContext,
    welcomeHandoff,
    toggleAnswer,
  };
}

export type OnboardingFlowController = ReturnType<typeof useOnboardingFlow>;

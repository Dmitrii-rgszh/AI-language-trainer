import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { defaultUserAccountDraft, type UserAccountDraft } from "../../entities/account/model";
import type { OnboardingAnswers, UserProfile } from "../../entities/user/model";
import { ApiError } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import {
  applyAdultSupportPreference,
  buildProfileDraft,
  cloneAnswers,
  fallbackProfessionTracks,
  goalOptions,
  inferLearnerPersona,
  learningContextOptions,
  skillFocusOptions,
  toggleValue,
  type OnboardingOption,
} from "../../shared/profile/profile-form-config";
import { applyGuestIntentToProfile, consumeGuestIntent } from "../../shared/profile/guest-intent";
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
    form.onboardingAnswers.primaryGoal.trim().length > 0 && form.professionTrack.trim().length > 0;
  const skillsReady = form.onboardingAnswers.activeSkillFocus.length > 0;
  const styleReady = form.lessonDuration >= 10 && form.lessonDuration <= 60;

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
              ? "Создай логин и укажи email, чтобы сохранить результат пробного урока и продолжить уже в личном пространстве обучения."
              : "Выбери логин и email, чтобы мы создали личное учебное пространство и сохранили ответы за правильным пользователем."
            : welcomeHandoff
              ? "Create your login and email so we can save the proof-lesson result and continue inside your personal learning space."
              : "Choose a login and email so we can create a private learner workspace and save onboarding answers under the right person.",
        ready: accountReady,
        helper:
          locale === "ru"
            ? welcomeHandoff
              ? "Укажи логин и email, и мы сразу привяжем к ним твой стартовый результат."
              : "Сначала добавь корректный логин и email."
            : welcomeHandoff
              ? "Add your login and email first so we can attach your starter result to the new workspace."
              : "Add a valid login and email first.",
      },
      {
        title: tr("Basics"),
        description: tr(
          "Set the learner name, languages, and target level so explanations and lesson pacing start in the right place.",
        ),
        ready: basicsReady,
        helper: tr("Add a learner name to continue."),
      },
      {
        title: tr("Learner"),
        description: tr("Tell us the learner's age and where English is most needed right now."),
        ready: true,
        helper: tr("Choose the age group and the main context."),
      },
      {
        title: tr("Goals"),
        description: tr("Choose the strongest outcomes and the first content lane to shape the starting lesson pack."),
        ready: goalsReady,
        helper: tr("Pick a main goal and a first content lane."),
      },
      {
        title: tr("Skills"),
        description: tr("Balance the engine between speaking, grammar, track depth, and the skills this learner needs most."),
        ready: skillsReady,
        helper: tr("Select at least one active skill focus."),
      },
      {
        title: tr("Style"),
        description: tr("Tune the rhythm, support needs, and topics so the trainer feels gentle, useful, and personal."),
        ready: styleReady,
        helper: tr("Keep lesson duration between 10 and 60 minutes."),
      },
      {
        title: tr("Review"),
        description: tr("Check the summary before we open the personal dashboard and the first lesson track."),
        ready: accountReady && basicsReady && goalsReady && skillsReady && styleReady,
        helper: tr("Review the setup and create the workspace."),
      },
    ],
    [
      accountReady,
      basicsReady,
      goalsReady,
      locale,
      skillsReady,
      styleReady,
      tr,
      welcomeHandoff,
    ],
  );

  const activeStep = steps[step];
  const allCoreStepsReady = steps.slice(0, -1).every((item) => item.ready);
  const needsAdultSupportQuestion =
    form.onboardingAnswers.ageGroup === "child" || form.onboardingAnswers.ageGroup === "teen";
  const adultSupportEnabled = form.onboardingAnswers.studyPreferences.includes("parent_guided");

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

  const updateAgeGroup = (value: string) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: {
        ...current.onboardingAnswers,
        ageGroup: value,
        learnerPersona: inferLearnerPersona(value, current.onboardingAnswers.learningContext),
        studyPreferences:
          value === "child" || value === "teen"
            ? current.onboardingAnswers.studyPreferences
            : applyAdultSupportPreference(current.onboardingAnswers.studyPreferences, false),
      },
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

  const updateAdultSupport = (enabled: boolean) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: {
        ...current.onboardingAnswers,
        studyPreferences: applyAdultSupportPreference(current.onboardingAnswers.studyPreferences, enabled),
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
        profile: {
          ...form,
          name: form.name.trim(),
          onboardingAnswers: cloneAnswers(form.onboardingAnswers),
        },
      });
      clearWelcomeProofLessonHandoff();
      navigate(routes.dashboard);
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

  return {
    account,
    activeStep,
    activeStepHelper,
    activeTrack,
    adultSupportEnabled,
    allCoreStepsReady,
    emailCheck,
    form,
    goBack,
    goNext,
    handleLocaleChange,
    isSaving,
    loginCheck,
    needsAdultSupportQuestion,
    setAccount,
    setStep,
    step,
    steps,
    submit,
    submitError,
    tracks,
    updateAdultSupport,
    updateAgeGroup,
    updateAnswer,
    updateField,
    updateLearningContext,
    welcomeHandoff,
    toggleAnswer,
  };
}

export type OnboardingFlowController = ReturnType<typeof useOnboardingFlow>;

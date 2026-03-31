import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { defaultUserAccountDraft, type UserAccountDraft } from "../../entities/account/model";
import type { OnboardingAnswers, UserProfile } from "../../entities/user/model";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import type { ProfessionTrackCard } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { cn } from "../../shared/utils/cn";
import {
  ageGroupOptions,
  buildProfileDraft,
  cloneAnswers,
  fallbackProfessionTracks,
  goalOptions,
  interestTopicOptions,
  learningContextOptions,
  skillFocusOptions,
  studyPreferenceOptions,
  supportNeedOptions,
  toggleValue,
  type OnboardingOption,
} from "./profile-form-config";

const currentLevelOptions = ["A1", "A2", "B1", "B2", "C1"] as const;
const targetLevelOptions = ["A2", "B1", "B2", "C1", "C2"] as const;
const learnerAgeQuestionOptions = ageGroupOptions.filter((option) => option.value !== "family_plan");
const adultSupportOptions: Array<{ value: "yes" | "no"; label: string }> = [
  { value: "yes", label: "Yes, adult support helps" },
  { value: "no", label: "No, independent enough" },
];

function inferLearnerPersona(ageGroup: string, learningContext: string) {
  if (ageGroup === "family_plan") {
    return "parent_or_guardian";
  }

  if (learningContext === "career_growth") {
    return "professional_learner";
  }

  if (ageGroup === "child" || ageGroup === "teen" || learningContext === "school_support") {
    return "school_learner";
  }

  return "self_learner";
}

function applyAdultSupportPreference(studyPreferences: string[], enabled: boolean) {
  if (enabled) {
    return studyPreferences.includes("parent_guided") ? studyPreferences : [...studyPreferences, "parent_guided"];
  }

  return studyPreferences.filter((item) => item !== "parent_guided");
}

function StepRailButton({
  index,
  title,
  active,
  completed,
  unlocked,
  onClick,
}: {
  index: number;
  title: string;
  active: boolean;
  completed: boolean;
  unlocked: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!unlocked}
      className={cn(
        "flex w-full items-center gap-3 rounded-[24px] border px-4 py-3 text-left transition-all",
        active
          ? "border-accent/50 bg-white text-ink shadow-soft"
          : "border-white/50 bg-white/50 text-slate-700 hover:bg-white",
        !unlocked && "cursor-not-allowed opacity-60 hover:bg-white/50",
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
          active
            ? "bg-accent text-white"
            : completed
              ? "bg-teal-100 text-teal-800"
              : "bg-sand/90 text-slate-700",
        )}
      >
        {completed ? "OK" : index + 1}
      </div>
      <div className="text-sm font-semibold">{title}</div>
    </button>
  );
}

function ChoiceCard({
  title,
  subtitle,
  active,
  onClick,
  delay = 0,
}: {
  title: string;
  subtitle?: string;
  active: boolean;
  onClick: () => void;
  delay?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{ animationDelay: `${delay}ms` }}
      className={cn(
        "onboarding-stagger-item rounded-[26px] border px-4 py-4 text-left transition-all",
        active
          ? "border-accent/50 bg-accent/10 text-ink shadow-soft"
          : "border-white/60 bg-white/70 text-slate-700 hover:-translate-y-0.5 hover:bg-white",
      )}
    >
      <div className="text-sm font-semibold">{title}</div>
      {subtitle ? <div className="mt-2 text-sm leading-6 text-slate-500">{subtitle}</div> : null}
    </button>
  );
}

function MetricSlider({
  label,
  value,
  onChange,
  delay = 0,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  delay?: number;
}) {
  return (
    <label
      style={{ animationDelay: `${delay}ms` }}
      className="onboarding-stagger-item block rounded-[24px] border border-white/60 bg-white/70 p-4 text-sm text-slate-700"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="font-semibold text-ink">{label}</span>
        <span className="rounded-full bg-sand px-3 py-1 text-xs font-semibold text-slate-700">{value}/10</span>
      </div>
      <input
        type="range"
        min={1}
        max={10}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-4 w-full accent-[#0f766e]"
      />
    </label>
  );
}

function resolveOptionLabel(value: string, options: OnboardingOption[], tr: (value: string) => string) {
  return tr(options.find((option) => option.value === value)?.label ?? value);
}

function resolveOptionList(values: string[], options: OnboardingOption[], tr: (value: string) => string) {
  if (values.length === 0) {
    return tr("Not set yet");
  }

  return values.map((value) => resolveOptionLabel(value, options, tr)).join(", ");
}

export function OnboardingScreen() {
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
    setForm((current) =>
      current.preferredUiLanguage === locale ? current : { ...current, preferredUiLanguage: locale },
    );
  }, [locale]);

  const tracks = professionTracks.length > 0 ? professionTracks : fallbackProfessionTracks;
  const activeTrack = useMemo(
    () => tracks.find((track) => track.domain === form.professionTrack) ?? tracks[0],
    [form.professionTrack, tracks],
  );

  const accountReady = account.login.trim().length >= 3 && account.email.includes("@");
  const basicsReady = form.name.trim().length > 0;
  const goalsReady = form.onboardingAnswers.primaryGoal.trim().length > 0 && form.professionTrack.trim().length > 0;
  const skillsReady = form.onboardingAnswers.activeSkillFocus.length > 0;
  const styleReady = form.lessonDuration >= 10 && form.lessonDuration <= 60;

  const steps = [
    {
      title: tr("User account"),
      description: tr(
        "Pick a login and email so we can create a private learner workspace and save onboarding answers under the right person.",
      ),
      ready: accountReady,
      helper: tr("Add a valid login and email first."),
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
  ];

  const activeStep = steps[step];
  const allCoreStepsReady = steps.slice(0, -1).every((item) => item.ready);
  const needsAdultSupportQuestion =
    form.onboardingAnswers.ageGroup === "child" || form.onboardingAnswers.ageGroup === "teen";
  const adultSupportEnabled = form.onboardingAnswers.studyPreferences.includes("parent_guided");

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
  const toggleAnswer = (
    field: "secondaryGoals" | "activeSkillFocus" | "studyPreferences" | "supportNeeds" | "interestTopics",
    value: string,
  ) =>
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

  const submit = async () => {
    if (!allCoreStepsReady) {
      return;
    }

    setIsSaving(true);
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
      navigate(routes.dashboard);
    } finally {
      setIsSaving(false);
    }
  };

  const renderOptionGrid = (
    options: OnboardingOption[],
    value: string,
    onSelect: (nextValue: string) => void,
    multi = false,
    selectedValues: string[] = [],
  ) => (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {options.map((option, index) => (
        <ChoiceCard
          key={option.value}
          title={tr(option.label)}
          active={multi ? selectedValues.includes(option.value) : value === option.value}
          onClick={() => onSelect(option.value)}
          delay={index * 55}
        />
      ))}
    </div>
  );

  const renderTrackGrid = (items: ProfessionTrackCard[]) => (
    <div className="grid gap-3 md:grid-cols-2">
      {items.map((track, index) => (
        <ChoiceCard
          key={track.id}
          title={tr(track.title)}
          subtitle={tr(track.summary)}
          active={form.professionTrack === track.domain}
          onClick={() => updateField("professionTrack", track.domain)}
          delay={index * 65}
        />
      ))}
    </div>
  );

  const renderStepContent = () => {
    if (step === 0) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
            <span>{tr("Login")}</span>
            <input
              value={account.login}
              onChange={(event) => setAccount((current) => ({ ...current, login: event.target.value }))}
              placeholder={tr("Choose a login")}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            />
          </label>
          <label
            style={{ animationDelay: "60ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700"
          >
            <span>{tr("Email")}</span>
            <input
              type="email"
              value={account.email}
              onChange={(event) => setAccount((current) => ({ ...current, email: event.target.value }))}
              placeholder={tr("name@example.com")}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            />
          </label>
          <div
            style={{ animationDelay: "120ms" }}
            className="onboarding-stagger-item rounded-[24px] border border-dashed border-accent/30 bg-accent/5 p-4 text-sm leading-6 text-slate-700 md:col-span-2"
          >
            {tr(
              "This is the only setup screen the learner sees before entering the real workspace. Once it is complete, the dashboard and lesson track open automatically.",
            )}
          </div>
        </div>
      );
    }

    if (step === 1) {
      return (
        <div className="grid gap-4 md:grid-cols-2">
          <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700 md:col-span-2">
            <span>{tr("Name or profile label")}</span>
            <input
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
              placeholder={tr("Your name")}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            />
          </label>
          <label
            style={{ animationDelay: "60ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700"
          >
            <span>{tr("Native language")}</span>
            <select
              value={form.nativeLanguage}
              onChange={(event) => updateField("nativeLanguage", event.target.value)}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            >
              <option value="ru">{tr("Russian")}</option>
              <option value="en">{tr("English")}</option>
              <option value="other">{tr("Other language")}</option>
            </select>
          </label>
          <label
            style={{ animationDelay: "120ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700"
          >
            <span>{tr("UI language")}</span>
            <select
              value={form.preferredUiLanguage}
              onChange={(event) => handleLocaleChange(event.target.value === "en" ? "en" : "ru")}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            >
              <option value="ru">{tr("Russian")}</option>
              <option value="en">{tr("English")}</option>
            </select>
          </label>
          <label
            style={{ animationDelay: "180ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700"
          >
            <span>{tr("Current level")}</span>
            <select
              value={form.currentLevel}
              onChange={(event) => updateField("currentLevel", event.target.value)}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            >
              {currentLevelOptions.map((level) => (
                <option key={level}>{level}</option>
              ))}
            </select>
          </label>
          <label
            style={{ animationDelay: "240ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700"
          >
            <span>{tr("Target level")}</span>
            <select
              value={form.targetLevel}
              onChange={(event) => updateField("targetLevel", event.target.value)}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            >
              {targetLevelOptions.map((level) => (
                <option key={level}>{level}</option>
              ))}
            </select>
          </label>
          <label
            style={{ animationDelay: "300ms" }}
            className="onboarding-stagger-item space-y-2 text-sm text-slate-700 md:col-span-2"
          >
            <span>{tr("Explanation language")}</span>
            <select
              value={form.preferredExplanationLanguage}
              onChange={(event) => updateField("preferredExplanationLanguage", event.target.value)}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            >
              <option value="ru">{tr("Russian")}</option>
              <option value="en">{tr("English")}</option>
            </select>
          </label>
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Learner age group")}</div>
            {renderOptionGrid(
              learnerAgeQuestionOptions,
              form.onboardingAnswers.ageGroup,
              (value) => updateAgeGroup(value),
            )}
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Where is English most needed right now?")}</div>
            {renderOptionGrid(
              learningContextOptions,
              form.onboardingAnswers.learningContext,
              (value) => updateLearningContext(value),
            )}
          </div>
          {needsAdultSupportQuestion ? (
            <div className="space-y-3">
              <div className="text-sm font-semibold text-ink">{tr("Does the learner need adult support?")}</div>
              <div className="grid gap-3 md:grid-cols-2">
                {adultSupportOptions.map((option, index) => (
                  <ChoiceCard
                    key={option.value}
                    title={tr(option.label)}
                    active={adultSupportEnabled === (option.value === "yes")}
                    onClick={() => updateAdultSupport(option.value === "yes")}
                    delay={index * 55}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      );
    }

    if (step === 3) {
      return (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Primary goal")}</div>
            {renderOptionGrid(goalOptions, form.onboardingAnswers.primaryGoal, (value) => updateAnswer("primaryGoal", value))}
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Secondary goals")}</div>
            {renderOptionGrid(
              goalOptions,
              "",
              (value) => toggleAnswer("secondaryGoals", value),
              true,
              form.onboardingAnswers.secondaryGoals,
            )}
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Content lane for the first lesson pack")}</div>
            {renderTrackGrid(tracks)}
          </div>
        </div>
      );
    }

    if (step === 4) {
      return (
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("What should the plan train most?")}</div>
            {renderOptionGrid(
              skillFocusOptions,
              "",
              (value) => toggleAnswer("activeSkillFocus", value),
              true,
              form.onboardingAnswers.activeSkillFocus,
            )}
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <MetricSlider
              label={tr("Speaking priority")}
              value={form.speakingPriority}
              onChange={(value) => updateField("speakingPriority", value)}
            />
            <MetricSlider
              label={tr("Grammar priority")}
              value={form.grammarPriority}
              onChange={(value) => updateField("grammarPriority", value)}
              delay={70}
            />
            <MetricSlider
              label={tr("Track priority")}
              value={form.professionPriority}
              onChange={(value) => updateField("professionPriority", value)}
              delay={140}
            />
          </div>
        </div>
      );
    }

    if (step === 5) {
      return (
        <div className="space-y-6">
          <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
            <span>{tr("Lesson duration")}</span>
            <input
              type="number"
              min={10}
              max={60}
              value={form.lessonDuration}
              onChange={(event) => updateField("lessonDuration", Number(event.target.value))}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            />
          </label>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Study preferences")}</div>
            {renderOptionGrid(
              studyPreferenceOptions,
              "",
              (value) => toggleAnswer("studyPreferences", value),
              true,
              form.onboardingAnswers.studyPreferences,
            )}
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Support needs")}</div>
            {renderOptionGrid(
              supportNeedOptions,
              "",
              (value) => toggleAnswer("supportNeeds", value),
              true,
              form.onboardingAnswers.supportNeeds,
            )}
          </div>
          <div className="space-y-3">
            <div className="text-sm font-semibold text-ink">{tr("Interest topics")}</div>
            {renderOptionGrid(
              interestTopicOptions,
              "",
              (value) => toggleAnswer("interestTopics", value),
              true,
              form.onboardingAnswers.interestTopics,
            )}
          </div>
          <label className="space-y-2 text-sm text-slate-700">
            <span>{tr("Flexible notes")}</span>
            <textarea
              rows={4}
              value={form.onboardingAnswers.notes}
              onChange={(event) => updateAnswer("notes", event.target.value)}
              placeholder={tr("Add anything important: special goals, child-safe preferences, exam target, or personal context.")}
              className="w-full rounded-[22px] border border-white/70 bg-white/80 px-4 py-3 outline-none transition focus:border-accent/50"
            />
          </label>
        </div>
      );
    }

    return (
      <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4">
          <div className="rounded-[26px] border border-white/60 bg-white/70 p-5">
            <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("Account")}</div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Login")}</div>
                <div className="mt-2 font-semibold text-ink">{account.login || tr("Not set yet")}</div>
              </div>
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Email")}</div>
                <div className="mt-2 font-semibold text-ink">{account.email || tr("Not set yet")}</div>
              </div>
            </div>
          </div>
          <div className="rounded-[26px] border border-white/60 bg-white/70 p-5">
            <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("Profile summary")}</div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Study format")}</div>
                <div className="mt-2 font-semibold text-ink">
                  {needsAdultSupportQuestion && adultSupportEnabled
                    ? tr("With adult support")
                    : tr("Independent format")}
                </div>
              </div>
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Age group")}</div>
                <div className="mt-2 font-semibold text-ink">
                  {resolveOptionLabel(form.onboardingAnswers.ageGroup, ageGroupOptions, tr)}
                </div>
              </div>
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Primary goal")}</div>
                <div className="mt-2 font-semibold text-ink">
                  {resolveOptionLabel(form.onboardingAnswers.primaryGoal, goalOptions, tr)}
                </div>
              </div>
              <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Learning context")}</div>
                <div className="mt-2 font-semibold text-ink">
                  {resolveOptionLabel(form.onboardingAnswers.learningContext, learningContextOptions, tr)}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[26px] border border-white/60 bg-white/70 p-5 text-sm leading-6 text-slate-700">
            <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("Current setup")}</div>
            <div className="mt-3 text-lg font-semibold text-ink">{form.name.trim() || tr("This learner")}</div>
            <div className="mt-2">{`${form.currentLevel} -> ${form.targetLevel} · ${tr(activeTrack?.title ?? form.professionTrack)}`}</div>
            <div className="mt-4 rounded-[20px] bg-white/80 px-4 py-3">
              {`${tr("Saved skill focus")}: ${resolveOptionList(form.onboardingAnswers.activeSkillFocus, skillFocusOptions, tr)}`}
            </div>
            <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
              {`${tr("Lesson format")}: ${form.lessonDuration} ${tr("minutes")}, ${tr("explanations in")} ${tr(
                form.preferredExplanationLanguage === "ru" ? "Russian" : "English",
              )}.`}
            </div>
            <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
              {`${tr("Current engine mix")}: ${tr("speaking")} ${form.speakingPriority}, ${tr("grammar")} ${form.grammarPriority}, ${tr("track")} ${form.professionPriority}.`}
            </div>
          </div>
          <div className="rounded-[26px] border border-dashed border-accent/30 bg-accent/5 p-5 text-sm leading-6 text-slate-700">
            {tr(
              "After this step, the learner gets a private dashboard, a first lesson lane, and profile-aware recommendations instead of demo placeholders.",
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
      <Card className="onboarding-hero relative overflow-hidden p-0">
        <div className="border-b border-white/50 px-5 py-5">
          <div className="max-w-[20rem]">
            <div className="text-xs uppercase tracking-[0.28em] text-teal-200">{tr("AI English Trainer Pro")}</div>
            <div className="mt-4 text-3xl font-semibold leading-tight text-white">
              {tr("Create a calm, personal start")}
            </div>
            <div className="mt-4 text-sm leading-6 text-slate-200">
              {tr(
                "This setup replaces the regular workspace until onboarding is complete, so the learner sees only the questions that matter right now.",
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4 px-5 py-5">
          <div className="rounded-[24px] bg-white/12 p-4 text-sm leading-6 text-white/90">
            {tr(
              "Build a flexible learner profile for adults, children, career goals, school support, and future multi-user use cases.",
            )}
          </div>

          <div className="space-y-3">
            {steps.map((item, index) => (
              <StepRailButton
                key={item.title}
                index={index}
                title={item.title}
                active={index === step}
                completed={index < step && item.ready}
                unlocked={index <= step}
                onClick={() => setStep(index)}
              />
            ))}
          </div>

          <div className="rounded-[24px] bg-white/12 p-4 text-sm leading-6 text-white/90">
            <div className="text-xs uppercase tracking-[0.24em] text-white/60">{tr("What unlocks after setup")}</div>
            <div className="mt-3">{tr("Private learner space")}</div>
            <div>{tr("Skill-balanced lesson track")}</div>
            <div>{tr("Friendly daily dashboard")}</div>
          </div>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-white/50 px-6 py-5">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.34em] text-coral">{`${tr("Step")} ${step + 1}/${steps.length}`}</div>
              <div className="mt-3 text-3xl font-semibold text-ink">{activeStep.title}</div>
              <div className="mt-3 max-w-[46rem] text-sm leading-6 text-slate-600">{activeStep.description}</div>
            </div>
            <div className="min-w-[220px] rounded-[24px] bg-white/70 px-4 py-4">
              <div className="flex items-center justify-between text-sm text-slate-600">
                <span>{tr("Completion")}</span>
                <span>{Math.round(((step + 1) / steps.length) * 100)}%</span>
              </div>
              <div className="mt-3 h-2 rounded-full bg-white">
                <div
                  className="h-full rounded-full bg-accent transition-all duration-500"
                  style={{ width: `${((step + 1) / steps.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          <div key={step} className="onboarding-step-panel">
            {renderStepContent()}
          </div>
        </div>

        <div className="border-t border-white/50 px-6 py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="text-sm leading-6 text-slate-500">{activeStep.helper}</div>
            <div className="flex flex-wrap items-center gap-3">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setStep((current) => Math.max(0, current - 1))}
                disabled={step === 0 || isSaving}
              >
                {tr("Back")}
              </Button>
              {step === steps.length - 1 ? (
                <Button type="button" onClick={() => void submit()} disabled={!allCoreStepsReady || isSaving}>
                  {isSaving ? tr("Saving...") : tr("Create workspace")}
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={() => setStep((current) => Math.min(steps.length - 1, current + 1))}
                  disabled={!activeStep.ready || isSaving}
                >
                  {tr("Continue")}
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

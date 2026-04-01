import { useEffect, useMemo, useState } from "react";
import type { OnboardingAnswers, UserProfile } from "../../entities/user/model";
import { useLocale } from "../../shared/i18n/useLocale";
import { ageGroupOptions, buildProfileDraft, cloneAnswers, fallbackProfessionTracks, goalOptions, interestTopicOptions, learnerPersonaOptions, learningContextOptions, skillFocusOptions, studyPreferenceOptions, supportNeedOptions, toggleValue, type OnboardingOption } from "../../shared/profile/profile-form-config";
import type { ProfessionTrackCard } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

function OptionButton({
  active,
  title,
  subtitle,
  onClick,
}: {
  active: boolean;
  title: string;
  subtitle?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-3xl border px-4 py-4 text-left transition-colors ${
        active ? "border-accent bg-accent/10 text-ink" : "border-white/70 bg-white/70 text-slate-700 hover:bg-white"
      }`}
    >
      <div className="text-sm font-semibold">{title}</div>
      {subtitle ? <div className="mt-1 text-xs leading-5 text-slate-500">{subtitle}</div> : null}
    </button>
  );
}

interface ProfileEditorCardProps {
  initialProfile: UserProfile | null;
  professionTracks: ProfessionTrackCard[];
  title: string;
  description: string;
  submitLabel: string;
  submitDisabled?: boolean;
  submitHelperText?: string;
  onSave: (profile: UserProfile) => Promise<void>;
}

export function ProfileEditorCard({
  initialProfile,
  professionTracks,
  title,
  description,
  submitLabel,
  submitDisabled = false,
  submitHelperText,
  onSave,
}: ProfileEditorCardProps) {
  const { tr } = useLocale();
  const [form, setForm] = useState<UserProfile>(() => buildProfileDraft(initialProfile));
  const [step, setStep] = useState(0);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    setForm(buildProfileDraft(initialProfile));
    setStep(0);
  }, [initialProfile]);

  const tracks = professionTracks.length > 0 ? professionTracks : fallbackProfessionTracks;
  const activeTrack = useMemo(
    () => tracks.find((track) => track.domain === form.professionTrack) ?? tracks[0],
    [tracks, form.professionTrack],
  );

  const resolveLabel = (value: string, options: OnboardingOption[]) =>
    tr(options.find((option) => option.value === value)?.label ?? value);
  const resolveLabels = (values: string[], options: OnboardingOption[]) =>
    values.map((value) => resolveLabel(value, options)).join(", ");

  const updateField = <K extends keyof UserProfile>(field: K, value: UserProfile[K]) => setForm((current) => ({ ...current, [field]: value }));
  const updateAnswer = <K extends keyof OnboardingAnswers>(field: K, value: OnboardingAnswers[K]) =>
    setForm((current) => ({ ...current, onboardingAnswers: { ...current.onboardingAnswers, [field]: value } }));
  const toggleAnswer = (field: "secondaryGoals" | "activeSkillFocus" | "studyPreferences" | "supportNeeds" | "interestTopics", value: string) =>
    setForm((current) => ({
      ...current,
      onboardingAnswers: { ...current.onboardingAnswers, [field]: toggleValue(current.onboardingAnswers[field], value) },
    }));

  const steps = [
    { title: tr("Basics"), ready: form.name.trim().length > 0 },
    { title: tr("Learner"), ready: true },
    { title: tr("Goals"), ready: true },
    { title: tr("Skills"), ready: form.onboardingAnswers.activeSkillFocus.length > 0 },
    { title: tr("Style"), ready: true },
    { title: tr("Review"), ready: true },
  ];

  const renderOptions = (
    options: OnboardingOption[],
    value: string,
    onSelect: (nextValue: string) => void,
    multi = false,
    selectedValues: string[] = [],
  ) => (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {options.map((option) => (
        <OptionButton
          key={option.value}
          active={multi ? selectedValues.includes(option.value) : value === option.value}
          title={tr(option.label)}
          onClick={() => onSelect(option.value)}
        />
      ))}
    </div>
  );

  const pages = [
    <div key="basics" className="grid gap-4 md:grid-cols-2">
      <label className="space-y-2 text-sm text-slate-700 md:col-span-2">
        <span>{tr("Name or profile label")}</span>
        <input value={form.name} onChange={(event) => updateField("name", event.target.value)} placeholder={tr("Your name")} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none" />
      </label>
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("Native language")}</span>
        <select value={form.nativeLanguage} onChange={(event) => updateField("nativeLanguage", event.target.value)} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none">
          <option value="ru">{tr("Russian")}</option>
          <option value="en">{tr("English")}</option>
          <option value="other">{tr("Other language")}</option>
        </select>
      </label>
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("UI language")}</span>
        <select value={form.preferredUiLanguage} onChange={(event) => updateField("preferredUiLanguage", event.target.value)} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none">
          <option value="ru">{tr("Russian")}</option>
          <option value="en">{tr("English")}</option>
        </select>
      </label>
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("Current level")}</span>
        <select value={form.currentLevel} onChange={(event) => updateField("currentLevel", event.target.value)} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none">
          <option>A1</option><option>A2</option><option>B1</option><option>B2</option><option>C1</option>
        </select>
      </label>
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("Target level")}</span>
        <select value={form.targetLevel} onChange={(event) => updateField("targetLevel", event.target.value)} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none">
          <option>A2</option><option>B1</option><option>B2</option><option>C1</option><option>C2</option>
        </select>
      </label>
      <label className="space-y-2 text-sm text-slate-700 md:col-span-2">
        <span>{tr("Explanation language")}</span>
        <select value={form.preferredExplanationLanguage} onChange={(event) => updateField("preferredExplanationLanguage", event.target.value)} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none">
          <option value="ru">{tr("Russian")}</option>
          <option value="en">{tr("English")}</option>
        </select>
      </label>
    </div>,
    <div key="learner" className="space-y-5">
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Who is this plan for?")}</div>{renderOptions(learnerPersonaOptions, form.onboardingAnswers.learnerPersona, (value) => updateAnswer("learnerPersona", value))}</div>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Age group")}</div>{renderOptions(ageGroupOptions, form.onboardingAnswers.ageGroup, (value) => updateAnswer("ageGroup", value))}</div>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Learning context")}</div>{renderOptions(learningContextOptions, form.onboardingAnswers.learningContext, (value) => updateAnswer("learningContext", value))}</div>
    </div>,
    <div key="goals" className="space-y-5">
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Primary goal")}</div>{renderOptions(goalOptions, form.onboardingAnswers.primaryGoal, (value) => updateAnswer("primaryGoal", value))}</div>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Secondary goals")}</div>{renderOptions(goalOptions, "", (value) => toggleAnswer("secondaryGoals", value), true, form.onboardingAnswers.secondaryGoals)}</div>
      <div className="space-y-3">
        <div className="text-sm font-semibold text-ink">{tr("Content lane for the first lesson pack")}</div>
        <div className="grid gap-3 md:grid-cols-2">
          {tracks.map((track) => (
            <OptionButton key={track.id} active={form.professionTrack === track.domain} title={tr(track.title)} subtitle={tr(track.summary)} onClick={() => updateField("professionTrack", track.domain)} />
          ))}
        </div>
      </div>
    </div>,
    <div key="skills" className="space-y-5">
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("What should the plan train most?")}</div>{renderOptions(skillFocusOptions, "", (value) => toggleAnswer("activeSkillFocus", value), true, form.onboardingAnswers.activeSkillFocus)}</div>
      <div className="rounded-3xl bg-white/70 p-4">
        <div className="text-sm font-semibold text-ink">{tr("Current engine mix")}</div>
        <div className="mt-4 space-y-4">
          <label className="block space-y-2 text-sm text-slate-700"><span>{tr("Speaking priority")}: {form.speakingPriority}/10</span><input type="range" min={1} max={10} value={form.speakingPriority} onChange={(event) => updateField("speakingPriority", Number(event.target.value))} className="w-full" /></label>
          <label className="block space-y-2 text-sm text-slate-700"><span>{tr("Grammar priority")}: {form.grammarPriority}/10</span><input type="range" min={1} max={10} value={form.grammarPriority} onChange={(event) => updateField("grammarPriority", Number(event.target.value))} className="w-full" /></label>
          <label className="block space-y-2 text-sm text-slate-700"><span>{tr("Track priority")}: {form.professionPriority}/10</span><input type="range" min={1} max={10} value={form.professionPriority} onChange={(event) => updateField("professionPriority", Number(event.target.value))} className="w-full" /></label>
        </div>
      </div>
    </div>,
    <div key="style" className="space-y-5">
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("Lesson duration")}</span>
        <input type="number" min={10} max={60} value={form.lessonDuration} onChange={(event) => updateField("lessonDuration", Number(event.target.value))} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none" />
      </label>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Study preferences")}</div>{renderOptions(studyPreferenceOptions, "", (value) => toggleAnswer("studyPreferences", value), true, form.onboardingAnswers.studyPreferences)}</div>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Support needs")}</div>{renderOptions(supportNeedOptions, "", (value) => toggleAnswer("supportNeeds", value), true, form.onboardingAnswers.supportNeeds)}</div>
      <div><div className="mb-2 text-sm font-semibold text-ink">{tr("Interest topics")}</div>{renderOptions(interestTopicOptions, "", (value) => toggleAnswer("interestTopics", value), true, form.onboardingAnswers.interestTopics)}</div>
      <label className="space-y-2 text-sm text-slate-700">
        <span>{tr("Flexible notes")}</span>
        <textarea rows={4} value={form.onboardingAnswers.notes} onChange={(event) => updateAnswer("notes", event.target.value)} placeholder={tr("Add anything important: special goals, child-safe preferences, exam target, or personal context.")} className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 outline-none" />
      </label>
    </div>,
    <div key="review" className="space-y-4">
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{`${form.name.trim() || tr("This learner")} ${tr("starts from")} ${form.currentLevel} ${tr("and moves to")} ${form.targetLevel}. ${tr("The first content lane is")} ${tr(activeTrack?.title ?? form.professionTrack)}.`}</div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700"><div className="text-xs uppercase tracking-[0.28em] text-slate-400">{tr("Learner type")}</div><div className="mt-2 font-medium text-ink">{resolveLabel(form.onboardingAnswers.learnerPersona, learnerPersonaOptions)}</div></div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700"><div className="text-xs uppercase tracking-[0.28em] text-slate-400">{tr("Age group")}</div><div className="mt-2 font-medium text-ink">{resolveLabel(form.onboardingAnswers.ageGroup, ageGroupOptions)}</div></div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700"><div className="text-xs uppercase tracking-[0.28em] text-slate-400">{tr("Primary goal")}</div><div className="mt-2 font-medium text-ink">{resolveLabel(form.onboardingAnswers.primaryGoal, goalOptions)}</div></div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700"><div className="text-xs uppercase tracking-[0.28em] text-slate-400">{tr("Learning context")}</div><div className="mt-2 font-medium text-ink">{resolveLabel(form.onboardingAnswers.learningContext, learningContextOptions)}</div></div>
      </div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Saved skill focus")}: {resolveLabels(form.onboardingAnswers.activeSkillFocus, skillFocusOptions)}</div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Study preferences")}: {resolveLabels(form.onboardingAnswers.studyPreferences, studyPreferenceOptions)}</div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Support needs")}: {resolveLabels(form.onboardingAnswers.supportNeeds, supportNeedOptions)}</div>
      {form.onboardingAnswers.notes.trim() ? <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{form.onboardingAnswers.notes}</div> : null}
    </div>,
  ];

  const submit = async () => {
    setIsSaving(true);
    try {
      await onSave({ ...form, name: form.name.trim(), onboardingAnswers: cloneAnswers(form.onboardingAnswers) });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Card className="space-y-5">
        <div className="flex flex-wrap gap-2">
          {steps.map((item, index) => (
            <button key={item.title} type="button" onClick={() => index <= step && setStep(index)} className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.24em] ${index === step ? "bg-accent text-white" : "bg-white/80 text-slate-700"}`}>{`${tr("Step")} ${index + 1}`}</button>
          ))}
        </div>
        <div className="h-2 rounded-full bg-white/60"><div className="h-full rounded-full bg-accent" style={{ width: `${((step + 1) / steps.length) * 100}%` }} /></div>
        <div><div className="text-xs uppercase tracking-[0.34em] text-coral">{`${tr("Step")} ${step + 1}/${steps.length}`}</div><div className="mt-2 text-2xl font-semibold text-ink">{steps[step].title}</div></div>
        {pages[step]}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Button variant="ghost" onClick={() => setStep((value) => Math.max(0, value - 1))} disabled={step === 0 || isSaving}>{tr("Back")}</Button>
          {step === steps.length - 1 ? (
            <Button onClick={() => void submit()} disabled={isSaving || submitDisabled || !steps.slice(0, -1).every((item) => item.ready)}>{isSaving ? tr("Saving...") : submitLabel}</Button>
          ) : (
            <Button onClick={() => setStep((value) => Math.min(steps.length - 1, value + 1))} disabled={!steps[step].ready || isSaving}>{tr("Continue")}</Button>
          )}
        </div>
        {submitDisabled && submitHelperText ? <div className="text-sm text-slate-500">{submitHelperText}</div> : null}
      </Card>

      <Card className="space-y-4">
        <div className="text-lg font-semibold text-ink">{title}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{description}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("This onboarding is designed to stay flexible for adults, teens, children, parent-guided study, and future multi-user product scenarios.")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{`${form.name.trim() || tr("This learner")} ${tr("is building a plan for")} ${resolveLabel(form.onboardingAnswers.primaryGoal, goalOptions)}. ${tr("The first content lane is")} ${tr(activeTrack?.title ?? form.professionTrack)}.`}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Saved skill focus")}: {resolveLabels(form.onboardingAnswers.activeSkillFocus, skillFocusOptions)}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Lesson format")}: {form.lessonDuration} {tr("minutes")}, {tr("explanations in")} {tr(form.preferredExplanationLanguage === "ru" ? "Russian" : "English")}.</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr("Current engine mix")}: {tr("speaking")} {form.speakingPriority}, {tr("grammar")} {form.grammarPriority}, {tr("track")} {form.professionPriority}.</div>
      </Card>
    </div>
  );
}

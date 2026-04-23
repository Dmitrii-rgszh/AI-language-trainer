import {
  currentLevelOptions,
  diagnosticReadinessOptions,
  emotionalBarrierOptions,
  englishRelationshipGoalOptions,
  goalOptions,
  learningContextOptions,
  preferredModeOptions,
  ritualElementOptions,
  resolveOptionLabel,
  resolveOptionList,
  skillFocusOptions,
  targetLevelOptions,
} from "../../shared/profile/profile-form-config";
import { cn } from "../../shared/utils/cn";
import { ChoiceCard, FieldStatusBadge } from "./OnboardingUi";
import type { OnboardingFlowController } from "./useOnboardingFlow";

type OnboardingStepContentProps = Pick<
  OnboardingFlowController,
  | "account"
  | "activeTrack"
  | "emailCheck"
  | "form"
  | "handleLocaleChange"
  | "loginCheck"
  | "setAccount"
  | "step"
  | "tracks"
  | "updateAnswer"
  | "updateField"
  | "updateLearningContext"
  | "toggleAnswer"
> & {
  tr: (value: string) => string;
};

function renderOptionGrid(
  options: Array<{ label: string; value: string }>,
  selectedValue: string,
  onSelect: (nextValue: string) => void,
  translate: (value: string) => string,
  multi = false,
  selectedValues: string[] = [],
) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {options.map((option, index) => (
        <ChoiceCard
          key={option.value}
          title={translate(option.label)}
          active={multi ? selectedValues.includes(option.value) : selectedValue === option.value}
          onClick={() => onSelect(option.value)}
          delay={index * 55}
        />
      ))}
    </div>
  );
}

function getLoginStatusPresentation(
  status: OnboardingFlowController["loginCheck"]["status"],
  loginValue: string,
  tr: (value: string) => string,
) {
  const fieldToneClass =
    status === "taken"
      ? "border-coral/40 bg-coral/5 focus:border-coral/70"
      : status === "available" || status === "existing_account"
        ? "border-accent/40 bg-accent/5 focus:border-accent/70"
        : "border-white/70 bg-white/80 focus:border-accent/50";

  const badgeClassName =
    status === "taken"
      ? "border-coral/20 bg-coral/8 text-coral"
      : status === "available" || status === "existing_account"
        ? "border-accent/20 bg-accent/8 text-accent"
        : "border-slate-200 bg-white/75 text-slate-500";

  const dotClassName =
    status === "taken"
      ? "bg-coral"
      : status === "available" || status === "existing_account"
        ? "bg-accent"
        : "bg-slate-400";

  const textClassName =
    status === "taken"
      ? "text-coral"
      : status === "available" || status === "existing_account"
        ? "text-accent"
        : "text-slate-500";

  const text =
    status === "checking"
      ? tr("Checking if this name is free...")
      : status === "available"
        ? tr("Nice choice, this name is free.")
        : status === "taken"
          ? tr("This name is already taken.")
          : status === "existing_account"
            ? tr("This looks like your existing account.")
            : status === "error"
              ? tr("We could not check this name right now.")
              : loginValue.trim().length > 0 && loginValue.trim().length < 3
                ? tr("Use at least 3 characters so we can check it.")
                : null;

  return {
    badgeClassName,
    dotClassName,
    fieldToneClass,
    text,
    textClassName,
  };
}

function getEmailStatusPresentation(
  status: OnboardingFlowController["emailCheck"]["status"],
  tr: (value: string) => string,
) {
  const fieldToneClass =
    status === "invalid"
      ? "border-coral/40 bg-coral/5 focus:border-coral/70"
      : status === "valid"
        ? "border-accent/40 bg-accent/5 focus:border-accent/70"
        : "border-white/70 bg-white/80 focus:border-accent/50";

  const badgeClassName =
    status === "invalid"
      ? "border-coral/20 bg-coral/8 text-coral"
      : status === "valid"
        ? "border-accent/20 bg-accent/8 text-accent"
        : "border-slate-200 bg-white/75 text-slate-500";

  const dotClassName = status === "valid" ? "bg-accent" : "bg-coral";

  const text =
    status === "valid"
      ? tr("Looks good, we will use this email for your account.")
      : status === "invalid"
        ? tr("Enter an email in the usual format, for example name@example.com.")
        : null;

  return {
    badgeClassName,
    dotClassName,
    fieldToneClass,
    text,
  };
}

export function OnboardingStepContent({
  account,
  activeTrack,
  emailCheck,
  form,
  handleLocaleChange,
  loginCheck,
  setAccount,
  step,
  tracks,
  tr,
  updateAnswer,
  updateField,
  updateLearningContext,
  toggleAnswer,
}: OnboardingStepContentProps) {
  const loginStatus = getLoginStatusPresentation(loginCheck.status, account.login, tr);
  const emailStatus = getEmailStatusPresentation(emailCheck.status, tr);

  if (step === 0) {
    return (
      <div className="grid gap-4 md:grid-cols-2">
        <div className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
          <label className="space-y-2">
            <span>{tr("Login")}</span>
            <input
              value={account.login}
              onChange={(event) => setAccount((current) => ({ ...current, login: event.target.value }))}
              placeholder={tr("Choose a login")}
              className={cn(
                "w-full rounded-[22px] border px-4 py-3 outline-none transition",
                loginStatus.fieldToneClass,
              )}
            />
          </label>
          {loginStatus.text ? (
            <FieldStatusBadge
              badgeClassName={loginStatus.badgeClassName}
              dotClassName={loginStatus.dotClassName}
              text={loginStatus.text}
              textClassName={loginStatus.textClassName}
            />
          ) : null}
          {loginCheck.status === "taken" && loginCheck.suggestions.length > 0 ? (
            <div className="rounded-[22px] border border-coral/15 bg-white/75 p-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                {tr("Try one of these free options")}
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {loginCheck.suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setAccount((current) => ({ ...current, login: suggestion }))}
                    className="rounded-full border border-accent/20 bg-accent/8 px-3 py-1.5 text-xs font-semibold text-ink transition-colors hover:border-accent/40 hover:bg-accent/14"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
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
            className={cn(
              "w-full rounded-[22px] border px-4 py-3 outline-none transition",
              emailStatus.fieldToneClass,
            )}
          />
          {emailStatus.text ? (
            <FieldStatusBadge
              badgeClassName={emailStatus.badgeClassName}
              dotClassName={emailStatus.dotClassName}
              text={emailStatus.text}
            />
          ) : null}
        </label>
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
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
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
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
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
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
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
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
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
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700 md:col-span-2">
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
          <div className="text-sm font-semibold text-ink">{tr("Primary goal")}</div>
          {renderOptionGrid(
            goalOptions,
            form.onboardingAnswers.primaryGoal,
            (value) => updateAnswer("primaryGoal", value),
            tr,
          )}
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Where is English most important right now?")}</div>
          {renderOptionGrid(
            learningContextOptions,
            form.onboardingAnswers.learningContext,
            updateLearningContext,
            tr,
          )}
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Content lane for the first daily loop")}</div>
          <div className="grid gap-3 md:grid-cols-2">
            {tracks.map((track, index) => (
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
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Preferred mode for the first loop")}</div>
          {renderOptionGrid(
            preferredModeOptions,
            form.onboardingAnswers.preferredMode,
            (value) => updateAnswer("preferredMode", value),
            tr,
          )}
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Diagnostic readiness")}</div>
          {renderOptionGrid(
            diagnosticReadinessOptions,
            form.onboardingAnswers.diagnosticReadiness,
            (value) => updateAnswer("diagnosticReadiness", value),
            tr,
          )}
        </div>
      </div>
    );
  }

  if (step === 3) {
    return (
      <div className="space-y-6">
        <label className="onboarding-stagger-item space-y-2 text-sm text-slate-700">
          <span>{tr("Time budget for the first daily loop")}</span>
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
          <div className="text-sm font-semibold text-ink">{tr("What should the first loops train most?")}</div>
          {renderOptionGrid(
            skillFocusOptions,
            "",
            (value) => toggleAnswer("activeSkillFocus", value),
            tr,
            true,
            form.onboardingAnswers.activeSkillFocus,
          )}
        </div>
      </div>
    );
  }

  if (step === 4) {
    return (
      <div className="space-y-6">
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("How should English feel in the long run?")}</div>
          {renderOptionGrid(
            englishRelationshipGoalOptions,
            form.onboardingAnswers.englishRelationshipGoal,
            (value) => updateAnswer("englishRelationshipGoal", value),
            tr,
          )}
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("What makes English feel heavy right now?")}</div>
          {renderOptionGrid(
            emotionalBarrierOptions,
            "",
            (value) => toggleAnswer("emotionalBarriers", value),
            tr,
            true,
            form.onboardingAnswers.emotionalBarriers,
          )}
        </div>
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Which rituals should become part of the route?")}</div>
          {renderOptionGrid(
            ritualElementOptions,
            "",
            (value) => toggleAnswer("ritualElements", value),
            tr,
            true,
            form.onboardingAnswers.ritualElements,
          )}
        </div>
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
          <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("First loop setup")}</div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Primary goal")}</div>
              <div className="mt-2 font-semibold text-ink">
                {resolveOptionLabel(form.onboardingAnswers.primaryGoal, goalOptions, tr)}
              </div>
            </div>
            <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Preferred mode")}</div>
              <div className="mt-2 font-semibold text-ink">
                {resolveOptionLabel(form.onboardingAnswers.preferredMode, preferredModeOptions, tr)}
              </div>
            </div>
            <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Diagnostic readiness")}</div>
              <div className="mt-2 font-semibold text-ink">
                {resolveOptionLabel(form.onboardingAnswers.diagnosticReadiness, diagnosticReadinessOptions, tr)}
              </div>
            </div>
            <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("Time budget")}</div>
              <div className="mt-2 font-semibold text-ink">
                {`${form.lessonDuration} ${tr("minutes")}`}
              </div>
            </div>
            <div className="rounded-[20px] bg-white/80 px-4 py-3 text-sm text-slate-700 md:col-span-2">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{tr("English relationship")}</div>
              <div className="mt-2 font-semibold text-ink">
                {resolveOptionLabel(form.onboardingAnswers.englishRelationshipGoal, englishRelationshipGoalOptions, tr)}
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
          <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
            {`${tr("First focus")}: ${resolveOptionList(form.onboardingAnswers.activeSkillFocus, skillFocusOptions, tr)}`}
          </div>
          <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
            {`${tr("Learning context")}: ${resolveOptionLabel(form.onboardingAnswers.learningContext, learningContextOptions, tr)}`}
          </div>
          <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
            {`${tr("First daily rhythm")}: ${resolveOptionLabel(form.onboardingAnswers.preferredMode, preferredModeOptions, tr)}, ${form.lessonDuration} ${tr("minutes")}.`}
          </div>
          <div className="mt-3 rounded-[20px] bg-white/80 px-4 py-3">
            {`${tr("English relationship")}: ${resolveOptionLabel(form.onboardingAnswers.englishRelationshipGoal, englishRelationshipGoalOptions, tr)}.`}
          </div>
        </div>
        <div className="rounded-[26px] border border-dashed border-accent/30 bg-accent/5 p-5 text-sm leading-6 text-slate-700">
          {tr(
            "After this step, the learner gets a personal dashboard and the first guided daily loop instead of a generic set of screens.",
          )}
        </div>
      </div>
    </div>
  );
}

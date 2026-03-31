import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { cn } from "../../shared/utils/cn";
import { type GuestDirectionId, writeGuestIntent } from "./guest-intent";

type WelcomeDirection = {
  id: GuestDirectionId;
  title: string;
  subtitle: string;
};

type MiniOnboardingOption = {
  value: string;
  title: string;
  subtitle: string;
};

const directionCards: WelcomeDirection[] = [
  {
    id: "speaking",
    title: "Speaking confidence",
    subtitle: "Start speaking more freely instead of freezing on simple phrases.",
  },
  {
    id: "grammar",
    title: "Grammar clarity",
    subtitle: "Fix the patterns that keep making your speech feel uncertain.",
  },
  {
    id: "vocabulary",
    title: "Vocabulary growth",
    subtitle: "Learn words you can actually reuse in daily conversations.",
  },
  {
    id: "reading",
    title: "Reading flow",
    subtitle: "Read faster and keep the meaning without translating every line.",
  },
  {
    id: "work",
    title: "English for work",
    subtitle: "Handle meetings, client language, and work messages in one place.",
  },
  {
    id: "travel",
    title: "Travel English",
    subtitle: "Feel calmer in airports, hotels, directions, and everyday trip situations.",
  },
  {
    id: "exam",
    title: "Exam focus",
    subtitle: "Build a cleaner route to tasks, structure, and measurable progress.",
  },
];

const painOptions: MiniOnboardingOption[] = [
  {
    value: "app_overload",
    title: "I am tired of jumping between different apps",
    subtitle: "I want one place for grammar, words, speaking, and progress.",
  },
  {
    value: "speaking_block",
    title: "I understand more than I can say",
    subtitle: "I know something already, but confidence breaks at the moment of speaking.",
  },
  {
    value: "forgetting",
    title: "I keep forgetting words and structures",
    subtitle: "I learn something, then lose it because there is no steady route.",
  },
  {
    value: "no_system",
    title: "I need a clear daily system",
    subtitle: "I want the platform to tell me what matters next instead of guessing alone.",
  },
];

const lessonToneOptions: MiniOnboardingOption[] = [
  {
    value: "quick_win",
    title: "Quick win in a few minutes",
    subtitle: "Show me the platform value fast and keep the first step light.",
  },
  {
    value: "guided",
    title: "Calm guided mini-lesson",
    subtitle: "I want a smooth first lesson with a clear sense of progress.",
  },
  {
    value: "diagnostic",
    title: "Smart diagnostic preview",
    subtitle: "Show me where my first strong result can come from.",
  },
];

const painTags = ["Speaking", "Grammar", "Vocabulary", "Reading", "Progress"] as const;

export function WelcomeScreen() {
  const [selectedDirections, setSelectedDirections] = useState<GuestDirectionId[]>([]);
  const [painPoint, setPainPoint] = useState<string>("");
  const [lessonTone, setLessonTone] = useState<string>("");
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const { tr } = useLocale();

  const selectedCards = useMemo(
    () => directionCards.filter((card) => selectedDirections.includes(card.id)),
    [selectedDirections],
  );
  const previewTitle =
    selectedCards.length > 0
      ? selectedCards.map((card) => tr(card.title)).join(" + ")
      : tr("Unified English route");
  const stepReady =
    step === 0 ? selectedDirections.length > 0 : step === 1 ? painPoint.length > 0 : lessonTone.length > 0;
  const stepProgress = ((step + 1) / 3) * 100;
  const selectionLimitReached = selectedDirections.length >= 3;

  const handleDirectionToggle = (id: GuestDirectionId) => {
    setSelectedDirections((current) => {
      if (current.includes(id)) {
        return current.filter((value) => value !== id);
      }

      if (current.length >= 3) {
        return current;
      }

      return [...current, id];
    });
  };

  const continueToOnboarding = () => {
    writeGuestIntent({
      directions: selectedDirections,
      painPoint,
      lessonTone,
    });
    navigate(routes.onboarding);
  };

  const activeStepTitle =
    step === 0
      ? tr("What do you want the platform to improve first?")
      : step === 1
        ? tr("What is the most annoying part of learning right now?")
        : tr("What should your first mini-lesson feel like?");
  const activeStepDescription =
    step === 0
      ? tr("Choose one to three directions so the first lesson starts from your real goal, not from a generic template.")
      : step === 1
        ? tr("Pick the pain that feels closest right now. We will use it as the emotional entry point for the first experience.")
        : tr("Choose the tone of the first experience. We will use it to shape the mini-lesson and the handoff into the full route.");

  return (
    <Card className="overflow-hidden border-white/70 p-0 shadow-soft">
      <div className="welcome-shell relative overflow-hidden px-6 py-6 lg:px-8 lg:py-8">
        <div className="welcome-shell__noise" />

        <div className="relative z-10">
          <header className="flex flex-col gap-4 border-b border-white/45 pb-5 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-ink text-sm font-semibold tracking-[0.28em] text-white">
                AI
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.28em] text-slate-500">{tr("AI English Trainer Pro")}</div>
                <div className="mt-1 text-sm text-slate-600">{tr("One platform instead of a stack of disconnected language tools.")}</div>
              </div>
            </div>

            <div className="rounded-full border border-accent/15 bg-white/75 px-4 py-2 text-sm font-medium text-slate-600">
              {tr("First lesson hook")} · {tr("3 short questions")}
            </div>
          </header>

          <div className="mt-8 grid gap-8 xl:grid-cols-[1.05fr_0.95fr] xl:items-center">
            <section className="max-w-[46rem]">
              <div className="text-xs uppercase tracking-[0.34em] text-coral">{tr("Stop searching")}</div>
              <h1 className="mt-5 max-w-[40rem] text-4xl font-semibold leading-[1.03] text-ink lg:text-[4.35rem]">
                {tr("You can stop searching for separate language apps.")}
              </h1>
              <p className="mt-5 max-w-[36rem] text-lg leading-8 text-slate-600">
                {tr(
                  "Grammar, vocabulary, speaking, reading, and progress can finally live in one calm system instead of a scattered stack of tools.",
                )}
              </p>

              <div className="mt-8 flex flex-wrap gap-2.5">
                {painTags.map((tag) => (
                  <div
                    key={tag}
                    className="rounded-full border border-white/60 bg-white/75 px-4 py-2 text-sm font-medium text-slate-700"
                  >
                    {tr(tag)}
                  </div>
                ))}
              </div>

              <div className="mt-10 grid gap-4 md:grid-cols-2">
                <div className="rounded-[26px] border border-white/55 bg-white/72 p-5">
                  <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("The pain")}</div>
                  <div className="mt-3 text-base font-semibold text-ink">
                    {tr("Most learners waste time building a personal stack of apps just to cover the basics.")}
                  </div>
                </div>
                <div className="rounded-[26px] border border-white/55 bg-white/72 p-5">
                  <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("The promise")}</div>
                  <div className="mt-3 text-base font-semibold text-ink">
                    {tr("This platform should replace that stack with one smarter route that adapts around you.")}
                  </div>
                </div>
              </div>

              <div className="mt-10 space-y-3 text-sm leading-7 text-slate-600">
                <div>{tr("Start with three light questions, see what the platform can tailor, and only then move deeper.")}</div>
                <div>{tr("The first lesson should already feel like relief: one place, one route, one clear next step.")}</div>
              </div>
            </section>

            <section className="rounded-[34px] border border-white/65 bg-white/82 p-5 shadow-soft backdrop-blur md:p-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-coral">{tr("Mini-onboarding")}</div>
                  <div className="mt-2 text-2xl font-semibold text-ink">{activeStepTitle}</div>
                </div>
                <div className="rounded-2xl bg-sand/80 px-4 py-3 text-right">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{tr("Step")}</div>
                  <div className="mt-1 text-lg font-semibold text-ink">{step + 1}/3</div>
                </div>
              </div>

              <div className="mt-4 h-2 rounded-full bg-sand/80">
                <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${stepProgress}%` }} />
              </div>

              <div className="mt-5 text-sm leading-6 text-slate-600">{activeStepDescription}</div>

              <div key={step} className="mt-6 onboarding-step-panel">
                {step === 0 ? (
                  <div className="grid gap-3 md:grid-cols-2">
                    {directionCards.map((card) => {
                      const active = selectedDirections.includes(card.id);
                      const disabled = !active && selectionLimitReached;

                      return (
                        <button
                          key={card.id}
                          type="button"
                          onClick={() => handleDirectionToggle(card.id)}
                          disabled={disabled}
                          className={cn(
                            "rounded-[24px] border px-4 py-4 text-left transition-all",
                            active
                              ? "border-accent/45 bg-accent/8 shadow-soft"
                              : "border-white/60 bg-[#fffaf4] hover:-translate-y-0.5 hover:bg-white",
                            disabled && "cursor-not-allowed opacity-45 hover:translate-y-0",
                          )}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="text-base font-semibold text-ink">{tr(card.title)}</div>
                            <div
                              className={cn(
                                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                                active ? "bg-accent text-white" : "bg-sand text-slate-600",
                              )}
                            >
                              {active ? selectedDirections.indexOf(card.id) + 1 : "+"}
                            </div>
                          </div>
                          <div className="mt-3 text-sm leading-6 text-slate-600">{tr(card.subtitle)}</div>
                        </button>
                      );
                    })}
                  </div>
                ) : null}

                {step === 1 ? (
                  <div className="space-y-3">
                    {painOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setPainPoint(option.value)}
                        className={cn(
                          "w-full rounded-[24px] border px-4 py-4 text-left transition-all",
                          painPoint === option.value
                            ? "border-accent/45 bg-accent/8 shadow-soft"
                            : "border-white/60 bg-[#fffaf4] hover:bg-white",
                        )}
                      >
                        <div className="text-base font-semibold text-ink">{tr(option.title)}</div>
                        <div className="mt-2 text-sm leading-6 text-slate-600">{tr(option.subtitle)}</div>
                      </button>
                    ))}
                  </div>
                ) : null}

                {step === 2 ? (
                  <div className="space-y-4">
                    {lessonToneOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setLessonTone(option.value)}
                        className={cn(
                          "w-full rounded-[24px] border px-4 py-4 text-left transition-all",
                          lessonTone === option.value
                            ? "border-accent/45 bg-accent/8 shadow-soft"
                            : "border-white/60 bg-[#fffaf4] hover:bg-white",
                        )}
                      >
                        <div className="text-base font-semibold text-ink">{tr(option.title)}</div>
                        <div className="mt-2 text-sm leading-6 text-slate-600">{tr(option.subtitle)}</div>
                      </button>
                    ))}

                    <div className="rounded-[24px] border border-dashed border-accent/20 bg-accent/5 p-4 text-sm leading-6 text-slate-700">
                      <div className="text-xs uppercase tracking-[0.22em] text-coral">{tr("Mini-lesson preview")}</div>
                      <div className="mt-3 text-lg font-semibold text-ink">{previewTitle}</div>
                      <div className="mt-2">
                        {tr("Your first route will start from these choices, then hand off into the deeper onboarding and your full learning workspace.")}
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>

              <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm leading-6 text-slate-500">
                  {step === 0
                    ? selectionLimitReached
                      ? tr("You already picked 3 directions. That is enough for a strong focused start.")
                      : tr("Choose one to three directions. A focused start works better than trying to fix everything.")
                    : step === 1
                      ? tr("Pick the frustration we should solve first. That is where the wow-effect should begin.")
                      : tr("Choose the tone, then we will carry this setup into your next step.")}
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button type="button" variant="ghost" disabled={step === 0} onClick={() => setStep((current) => current - 1)}>
                    {tr("Back")}
                  </Button>
                  {step < 2 ? (
                    <Button type="button" disabled={!stepReady} onClick={() => setStep((current) => current + 1)}>
                      {tr("Continue")}
                    </Button>
                  ) : (
                    <Button type="button" disabled={!stepReady || selectedDirections.length === 0} onClick={continueToOnboarding}>
                      {tr("Build my mini-lesson")}
                    </Button>
                  )}
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </Card>
  );
}

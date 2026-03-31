import { useState } from "react";
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
  { id: "speaking", title: "Speaking confidence", subtitle: "Start with speaking and real conversation confidence." },
  { id: "grammar", title: "Grammar clarity", subtitle: "Fix the grammar patterns that slow you down." },
  { id: "vocabulary", title: "Vocabulary growth", subtitle: "Learn words you can immediately reuse." },
  { id: "reading", title: "Reading flow", subtitle: "Read faster and keep the meaning more easily." },
  { id: "work", title: "English for work", subtitle: "Cover work tasks, meetings, and client language." },
  { id: "travel", title: "Travel English", subtitle: "Feel calmer in airports, hotels, and routes." },
  { id: "exam", title: "Exam focus", subtitle: "Build a cleaner path toward exam tasks." },
];

const painOptions: MiniOnboardingOption[] = [
  {
    value: "speaking_block",
    title: "I know something, but I freeze when I need to speak",
    subtitle: "I want the first lesson to unlock speaking confidence.",
  },
  {
    value: "forgetting",
    title: "I keep forgetting words and structures",
    subtitle: "I need a route that helps me remember and reuse.",
  },
  {
    value: "grammar_confusion",
    title: "I get lost in grammar and start doubting myself",
    subtitle: "I want clearer explanations and simple progress.",
  },
  {
    value: "app_overload",
    title: "I am tired of using different apps for different tasks",
    subtitle: "I want one place that closes the whole learning loop.",
  },
];

const lessonToneOptions: MiniOnboardingOption[] = [
  {
    value: "quick_win",
    title: "Give me a quick result",
    subtitle: "Show platform value in 1-2 minutes.",
  },
  {
    value: "guided",
    title: "Give me a calm guided tryout",
    subtitle: "I want a smooth first lesson with clear support.",
  },
  {
    value: "diagnostic",
    title: "Show me a smart skill snapshot",
    subtitle: "I want a short lesson plus a useful skill insight.",
  },
];

export function WelcomeScreen() {
  const [selectedDirections, setSelectedDirections] = useState<GuestDirectionId[]>([]);
  const [painPoint, setPainPoint] = useState("");
  const [lessonTone, setLessonTone] = useState("");
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const { tr } = useLocale();

  const selectionLimitReached = selectedDirections.length >= 3;
  const stepReady =
    step === 0 ? selectedDirections.length > 0 : step === 1 ? painPoint.length > 0 : lessonTone.length > 0;

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

  const continueFlow = () => {
    if (step < 2) {
      setStep((current) => current + 1);
      return;
    }

    writeGuestIntent({
      directions: selectedDirections,
      painPoint,
      lessonTone,
    });
    navigate(routes.onboarding);
  };

  const activeStepTitle =
    step === 0
      ? tr("What do you want to improve first?")
      : step === 1
        ? tr("What annoys you the most right now?")
        : tr("How should the first lesson feel?");

  const activeStepDescription =
    step === 0
      ? tr("Choose one to three directions for the first 1-2 minute lesson.")
      : step === 1
        ? tr("Choose the main friction so the first lesson solves something real.")
        : tr("Choose the tone of the first mini-lesson and quick skill snapshot.");

  return (
    <Card className="overflow-hidden border-white/70 p-0 shadow-soft">
      <div className="welcome-shell relative overflow-hidden px-6 py-6 lg:px-8 lg:py-8">
        <div className="welcome-shell__noise" />

        <div className="relative z-10">
          <header className="flex items-center gap-3 border-b border-white/45 pb-5">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-ink text-sm font-semibold tracking-[0.28em] text-white">
              AI
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.28em] text-slate-500">{tr("AI English Trainer Pro")}</div>
              <div className="mt-1 text-sm text-slate-600">{tr("One platform instead of a stack of disconnected language tools.")}</div>
            </div>
          </header>

          <div className="mt-8 grid gap-8 xl:grid-cols-[1.02fr_0.98fr] xl:items-start">
            <section className="max-w-[44rem] pt-2">
              <div className="text-xs uppercase tracking-[0.34em] text-coral">{tr("Stop searching")}</div>
              <h1 className="mt-5 max-w-[40rem] text-4xl font-semibold leading-[1.03] text-ink lg:text-[4.25rem]">
                {tr("You can stop searching for separate language apps.")}
              </h1>
              <p className="mt-5 max-w-[35rem] text-lg leading-8 text-slate-600">
                {tr(
                  "Grammar, vocabulary, speaking, reading, and progress can finally live in one calm system instead of a scattered stack of tools.",
                )}
              </p>

              <div className="mt-8 grid gap-4 md:grid-cols-2">
                <div className="rounded-[28px] border border-white/60 bg-white/82 p-6 shadow-soft">
                  <div className="text-base font-semibold leading-8 text-ink">
                    {tr("This platform replaces that stack with one smarter route that adapts around you.")}
                  </div>
                </div>
                <div className="rounded-[28px] border border-accent/20 bg-accent/[0.06] p-6 shadow-soft">
                  <div className="text-base font-semibold leading-8 text-ink">
                    {tr("Your first lesson and skill snapshot start before payment or registration.")}
                  </div>
                </div>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                <div className="rounded-full border border-white/60 bg-white/78 px-4 py-2 text-sm font-medium text-slate-700">
                  {tr("Do not pay until you try it yourself.")}
                </div>
                <div className="rounded-full border border-white/60 bg-white/78 px-4 py-2 text-sm font-medium text-slate-700">
                  {tr("Do not register until you see the value.")}
                </div>
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
                <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${((step + 1) / 3) * 100}%` }} />
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
                              ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.95))] shadow-soft"
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
                            ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.96))] shadow-soft"
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
                  <div className="space-y-3">
                    {lessonToneOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => setLessonTone(option.value)}
                        className={cn(
                          "w-full rounded-[24px] border px-4 py-4 text-left transition-all",
                          lessonTone === option.value
                            ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.96))] shadow-soft"
                            : "border-white/60 bg-[#fffaf4] hover:bg-white",
                        )}
                      >
                        <div className="text-base font-semibold text-ink">{tr(option.title)}</div>
                        <div className="mt-2 text-sm leading-6 text-slate-600">{tr(option.subtitle)}</div>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="mt-6 rounded-[24px] border border-white/65 bg-[#fffaf4] p-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="max-w-[29rem] text-sm leading-6 text-slate-500">
                    {step === 0
                      ? tr("Choose one to three directions for the first 1-2 minute lesson.")
                      : step === 1
                        ? tr("Choose the main friction so the first lesson solves something real.")
                        : tr("Pick the tone, then start the first short lesson and see the result.")}
                  </div>

                  <div className="flex flex-wrap gap-3">
                    <Button type="button" variant="ghost" disabled={step === 0} onClick={() => setStep((current) => current - 1)}>
                      {tr("Back")}
                    </Button>
                    <Button type="button" disabled={!stepReady} onClick={continueFlow}>
                      {step === 2 ? tr("Build my mini-lesson") : tr("Continue")}
                    </Button>
                  </div>
                </div>
              </div>

              <div className="mt-4 text-sm leading-6 text-slate-500">
                {tr("A short lesson comes first. Registration and payment can wait until the value feels obvious.")}
              </div>
            </section>
          </div>
        </div>
      </div>
    </Card>
  );
}

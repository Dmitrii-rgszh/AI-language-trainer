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
  accent: string;
};

const directionCards: WelcomeDirection[] = [
  {
    id: "speaking",
    title: "Speaking confidence",
    subtitle: "Short real-life prompts, answers, and quick speaking support.",
    accent: "from-[#0f766e]/20 to-transparent",
  },
  {
    id: "grammar",
    title: "Grammar clarity",
    subtitle: "Fix the mistakes that slow your speech down in daily use.",
    accent: "from-[#c96b43]/20 to-transparent",
  },
  {
    id: "vocabulary",
    title: "Vocabulary growth",
    subtitle: "Useful words you can actually use, not random word lists.",
    accent: "from-[#4c7f5d]/20 to-transparent",
  },
  {
    id: "reading",
    title: "Reading flow",
    subtitle: "Understand texts faster and keep the main idea without stress.",
    accent: "from-[#7c5c9e]/18 to-transparent",
  },
  {
    id: "work",
    title: "English for work",
    subtitle: "Meetings, clients, messages, and confident professional wording.",
    accent: "from-[#1d4e89]/20 to-transparent",
  },
  {
    id: "travel",
    title: "Travel English",
    subtitle: "Phrases and confidence for airports, hotels, and everyday situations.",
    accent: "from-[#b45309]/20 to-transparent",
  },
  {
    id: "exam",
    title: "Exam focus",
    subtitle: "A cleaner route toward test tasks, structure, and steady progress.",
    accent: "from-[#9f1239]/18 to-transparent",
  },
];

function toggleDirection(selected: GuestDirectionId[], nextValue: GuestDirectionId) {
  return selected.includes(nextValue) ? selected.filter((value) => value !== nextValue) : [...selected, nextValue];
}

export function WelcomeScreen() {
  const [selectedDirections, setSelectedDirections] = useState<GuestDirectionId[]>([]);
  const navigate = useNavigate();
  const { tr } = useLocale();

  const selectedCards = useMemo(
    () => directionCards.filter((card) => selectedDirections.includes(card.id)),
    [selectedDirections],
  );
  const selectionLimitReached = selectedDirections.length >= 3;
  const previewTitle =
    selectedCards.length > 0
      ? selectedCards.map((card) => tr(card.title)).join(" + ")
      : tr("Personal English route");

  const handleSelect = (id: GuestDirectionId) => {
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
    writeGuestIntent({ directions: selectedDirections });
    navigate(routes.onboarding);
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
      <Card className="overflow-hidden p-0">
        <div className="welcome-stage relative overflow-hidden px-6 py-7 lg:px-8 lg:py-8">
          <div className="welcome-stage__grid" />
          <div className="relative z-10 max-w-[44rem]">
            <div className="text-xs uppercase tracking-[0.34em] text-teal-200">{tr("Start free")}</div>
            <h1 className="mt-4 max-w-[40rem] text-4xl font-semibold leading-tight text-white lg:text-[3.45rem]">
              {tr("Find your first useful English lesson before any registration.")}
            </h1>
            <p className="mt-5 max-w-[36rem] text-base leading-7 text-slate-200">
              {tr(
                "Pick one to three directions, and we will shape the first route around the result you want to feel right away.",
              )}
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <div className="rounded-full border border-white/18 bg-white/12 px-4 py-2 text-sm font-medium text-white/90">
                {tr("No account wall at the start")}
              </div>
              <div className="rounded-full border border-white/18 bg-white/12 px-4 py-2 text-sm font-medium text-white/90">
                {tr("Choose up to 3 focus areas")}
              </div>
              <div className="rounded-full border border-white/18 bg-white/12 px-4 py-2 text-sm font-medium text-white/90">
                {tr("Personal route starts from your picks")}
              </div>
            </div>
          </div>
        </div>
      </Card>

      <Card className="glass-panel overflow-hidden border border-white/60 p-0 shadow-soft">
        <div className="border-b border-white/50 px-6 py-5">
          <div className="text-xs uppercase tracking-[0.28em] text-coral">{tr("Pick your direction")}</div>
          <div className="mt-3 text-3xl font-semibold text-ink">{tr("What should this trainer help with first?")}</div>
          <div className="mt-3 max-w-[42rem] text-sm leading-6 text-slate-600">
            {tr("Choose from one to three goals. The first experience should feel relevant, light, and worth continuing.")}
          </div>
        </div>

        <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1fr_300px]">
          <div className="grid gap-3 md:grid-cols-2">
            {directionCards.map((card, index) => {
              const active = selectedDirections.includes(card.id);
              const disabled = !active && selectionLimitReached;

              return (
                <button
                  key={card.id}
                  type="button"
                  style={{ animationDelay: `${index * 45}ms` }}
                  onClick={() => handleSelect(card.id)}
                  disabled={disabled}
                  className={cn(
                    "onboarding-stagger-item relative overflow-hidden rounded-[28px] border p-4 text-left transition-all",
                    active
                      ? "border-accent/50 bg-white shadow-soft"
                      : "border-white/60 bg-white/78 hover:-translate-y-0.5 hover:bg-white",
                    disabled && "cursor-not-allowed opacity-45 hover:translate-y-0",
                  )}
                >
                  <div className={cn("absolute inset-0 bg-gradient-to-br opacity-80", card.accent)} />
                  <div className="relative z-10">
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-base font-semibold text-ink">{tr(card.title)}</div>
                      <div
                        className={cn(
                          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold",
                          active ? "bg-accent text-white" : "bg-sand text-slate-700",
                        )}
                      >
                        {active ? selectedDirections.indexOf(card.id) + 1 : "+"}
                      </div>
                    </div>
                    <div className="mt-3 text-sm leading-6 text-slate-600">{tr(card.subtitle)}</div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="space-y-4">
            <div className="rounded-[28px] border border-white/60 bg-white/80 p-5">
              <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("Your preview")}</div>
              <div className="mt-3 text-2xl font-semibold text-ink">{previewTitle}</div>
              <div className="mt-4 text-sm leading-6 text-slate-600">
                {selectedCards.length > 0
                  ? tr(
                      "Good start. We will carry these directions into the next setup so your route already leans toward what matters most.",
                    )
                  : tr("Choose at least one direction to build a more relevant first experience.")}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {selectedCards.length > 0 ? (
                  selectedCards.map((card) => (
                    <div key={card.id} className="rounded-full bg-accent/10 px-3 py-1.5 text-xs font-semibold text-accent">
                      {tr(card.title)}
                    </div>
                  ))
                ) : (
                  <div className="rounded-full bg-sand px-3 py-1.5 text-xs font-semibold text-slate-600">
                    {tr("1 to 3 choices")}
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-[28px] border border-dashed border-accent/25 bg-accent/5 p-5 text-sm leading-6 text-slate-700">
              <div>{tr("The full free lesson hook is the next layer we will shape around these picks.")}</div>
              <div className="mt-3">{tr("For now this first page already removes the cold account wall and starts from the learner's intention.")}</div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={continueToOnboarding} disabled={selectedDirections.length === 0}>
                {tr("Build my route")}
              </Button>
              <Button type="button" variant="secondary" onClick={() => navigate(routes.onboarding)}>
                {tr("Skip to full onboarding")}
              </Button>
            </div>

            {selectionLimitReached ? (
              <div className="text-sm leading-6 text-slate-500">
                {tr("You already picked 3 directions. Remove one if you want to swap the focus.")}
              </div>
            ) : (
              <div className="text-sm leading-6 text-slate-500">
                {tr("The strongest start usually comes from one to three priorities, not from trying to fix everything at once.")}
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

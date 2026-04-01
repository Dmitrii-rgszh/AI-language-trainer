import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { ConvergingPathsScrollIndicator } from "../../shared/ui/ConvergingPathsScrollIndicator";
import { Button } from "../../shared/ui/Button";
import { cn } from "../../shared/utils/cn";
import { type GuestDirectionId, writeGuestIntent } from "./guest-intent";
import { WelcomePremiumHeader } from "./WelcomePremiumHeader";
import { WelcomeSignInModal } from "./WelcomeSignInModal";
import { useWelcomeSignIn } from "./useWelcomeSignIn";
import {
  welcomeScrollIndicatorConfig,
  welcomeScrollIndicatorMessages,
} from "./welcomeScrollIndicator";

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

const HERO_PRIMARY_SCROLL_TARGET_ID = "welcome-mini-onboarding";
const HERO_WHEEL_TRIGGER_THRESHOLD = 72;
const HERO_TRACKPAD_TRIGGER_THRESHOLD = 148;
const HERO_WHEEL_DEBOUNCE_MS = 180;
const HERO_TRACKPAD_DEBOUNCE_MS = 260;
const HERO_WHEEL_COOLDOWN_MS = 1100;
const HERO_WHEEL_MAX_SCROLL_Y = 56;
const HERO_TRACKPAD_MICRO_SCROLL_THRESHOLD = 6;
const HERO_TRACKPAD_EVENT_DELTA_MAX = 32;

const heroPrimaryCtaLabel = {
  ru: "Собрать первый урок",
  en: "Build the first lesson",
} as const;

const heroScrollCueAriaLabel = {
  ru: "Прокрутите, чтобы увидеть, как Verba собирает обучение в одну систему",
  en: "Scroll to see how Verba brings learning into one system",
} as const;

export function WelcomeScreen() {
  const [selectedDirections, setSelectedDirections] = useState<GuestDirectionId[]>([]);
  const [painPoint, setPainPoint] = useState("");
  const [lessonTone, setLessonTone] = useState("");
  const [step, setStep] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const [heroVisible, setHeroVisible] = useState(false);
  const [wizardVisible, setWizardVisible] = useState(false);
  const navigate = useNavigate();
  const { locale, setLocale, tr } = useLocale();
  const signInView = useWelcomeSignIn(locale);
  const localeOptions = [
    { value: "ru" as const, label: "RU", flagClass: "locale-flag--ru" },
    { value: "en" as const, label: "EN", flagClass: "locale-flag--en" },
  ];
  const heroSectionRef = useRef<HTMLElement | null>(null);
  const onboardingSectionRef = useRef<HTMLElement | null>(null);
  const heroWheelAccumulatedDeltaRef = useRef(0);
  const heroWheelDebounceRef = useRef<number | null>(null);
  const heroWheelCooldownUntilRef = useRef(0);

  useEffect(() => {
    const animationFrame = window.requestAnimationFrame(() => setHeroVisible(true));
    return () => window.cancelAnimationFrame(animationFrame);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const sectionNode = onboardingSectionRef.current;
    if (!sectionNode) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setWizardVisible(true);
        }
      },
      { threshold: 0.22 },
    );

    observer.observe(sectionNode);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const heroNode = heroSectionRef.current;
    if (!heroNode) {
      return;
    }

    const resetWheelIntent = () => {
      heroWheelAccumulatedDeltaRef.current = 0;

      if (heroWheelDebounceRef.current !== null) {
        window.clearTimeout(heroWheelDebounceRef.current);
        heroWheelDebounceRef.current = null;
      }
    };

    const getHeroPrimaryScrollTarget = () =>
      document.getElementById(HERO_PRIMARY_SCROLL_TARGET_ID) ?? onboardingSectionRef.current;

    const triggerHeroSectionAdvance = () => {
      const targetSection = getHeroPrimaryScrollTarget();
      if (!targetSection) {
        return;
      }

      targetSection.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    };

    const handleWheel = (event: WheelEvent) => {
      if (event.ctrlKey || Math.abs(event.deltaY) <= Math.abs(event.deltaX) || event.deltaY <= 0) {
        resetWheelIntent();
        return;
      }

      const isLikelyTrackpad =
        event.deltaMode === WheelEvent.DOM_DELTA_PIXEL &&
        Math.abs(event.deltaY) <= HERO_TRACKPAD_EVENT_DELTA_MAX;

      if (isLikelyTrackpad && Math.abs(event.deltaY) < HERO_TRACKPAD_MICRO_SCROLL_THRESHOLD) {
        resetWheelIntent();
        return;
      }

      const heroRect = heroNode.getBoundingClientRect();
      const heroIsPrimaryViewport =
        window.scrollY <= HERO_WHEEL_MAX_SCROLL_Y &&
        heroRect.top <= 8 &&
        heroRect.bottom >= window.innerHeight * 0.55;

      if (!heroIsPrimaryViewport) {
        resetWheelIntent();
        return;
      }

      const now = performance.now();
      if (now < heroWheelCooldownUntilRef.current) {
        event.preventDefault();
        return;
      }

      const threshold = isLikelyTrackpad
        ? HERO_TRACKPAD_TRIGGER_THRESHOLD
        : HERO_WHEEL_TRIGGER_THRESHOLD;
      const debounceMs = isLikelyTrackpad
        ? HERO_TRACKPAD_DEBOUNCE_MS
        : HERO_WHEEL_DEBOUNCE_MS;
      const normalizedDelta = isLikelyTrackpad
        ? Math.max(0, event.deltaY - HERO_TRACKPAD_MICRO_SCROLL_THRESHOLD) * 0.9
        : event.deltaY;

      heroWheelAccumulatedDeltaRef.current += normalizedDelta;

      if (heroWheelDebounceRef.current !== null) {
        window.clearTimeout(heroWheelDebounceRef.current);
      }

      heroWheelDebounceRef.current = window.setTimeout(() => {
        heroWheelAccumulatedDeltaRef.current = 0;
        heroWheelDebounceRef.current = null;
      }, debounceMs);

      if (heroWheelAccumulatedDeltaRef.current < threshold) {
        return;
      }

      event.preventDefault();
      heroWheelCooldownUntilRef.current = now + HERO_WHEEL_COOLDOWN_MS;
      resetWheelIntent();
      triggerHeroSectionAdvance();
    };

    heroNode.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      heroNode.removeEventListener("wheel", handleWheel);
      resetWheelIntent();
    };
  }, []);

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

  const heroTheses = [
    {
      eyebrow: tr("One system"),
      title: tr("Everything for language learning in one calm system."),
    },
    {
      eyebrow: tr("Motivation"),
      title: tr("Motivation should go into learning, not platform search."),
    },
    {
      eyebrow: tr("Value first"),
      title: tr("The platform shows value first, and only then asks for details."),
    },
  ];

  const getHeroPrimaryScrollTarget = () =>
    document.getElementById(HERO_PRIMARY_SCROLL_TARGET_ID) ?? onboardingSectionRef.current;

  const handleHeroPrimaryAction = () => {
    const targetSection = getHeroPrimaryScrollTarget();

    targetSection?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      block: "start",
    });
  };

  return (
    <div className="welcome-story relative">
      <div
        className="welcome-parallax-orb welcome-parallax-orb--left"
        style={{ transform: `translate3d(0, ${scrollY * 0.12}px, 0)` }}
      />
      <div
        className="welcome-parallax-orb welcome-parallax-orb--right"
        style={{ transform: `translate3d(0, ${scrollY * -0.08}px, 0)` }}
      />

      <section
        ref={heroSectionRef}
        className="welcome-shell welcome-screen welcome-screen--hero relative px-6 py-6 lg:px-8 lg:py-8"
      >
        <div className="welcome-shell__noise" />

        <div className="relative z-10 flex min-h-[calc(100vh-3rem)] flex-col">
          <WelcomePremiumHeader
            accountPrompt={signInView.copy.accountPrompt}
            accountPromptCompact={signInView.copy.accountPromptCompact}
            continueWithAccount={signInView.copy.continueWithAccount}
            heroVisible={heroVisible}
            locale={locale}
            localeOptions={localeOptions}
            onOpenSignIn={signInView.open}
            setLocale={setLocale}
            tr={tr}
          />

          <div className="flex flex-1 items-center py-12 md:py-16 lg:py-24">
            <div className="grid w-full gap-8 xl:grid-cols-[minmax(0,1.04fr)_minmax(360px,0.82fr)] xl:items-center">
              <div className="max-w-[48rem]">
                <div className={cn("welcome-reveal text-xs uppercase tracking-[0.28em] text-coral", heroVisible && "is-visible")} style={{ transitionDelay: "90ms" }}>
                  {tr("Stop searching")}
                </div>
                <h1
                  className={cn(
                    "welcome-reveal mt-5 max-w-[42rem] text-4xl font-[700] leading-[0.99] tracking-[-0.05em] text-ink lg:text-[4.5rem]",
                    heroVisible && "is-visible",
                  )}
                  style={{ transitionDelay: "170ms" }}
                >
                  {tr("You no longer need to search for language-learning tools.")}
                </h1>
                <p
                  className={cn("welcome-reveal mt-5 max-w-[36rem] text-lg leading-8 text-slate-600", heroVisible && "is-visible")}
                  style={{ transitionDelay: "250ms" }}
                >
                  {tr("Language learning no longer has to be stitched together from separate tools.")}
                </p>
                <div
                  className={cn("welcome-reveal mt-7", heroVisible && "is-visible")}
                  style={{ transitionDelay: "330ms" }}
                >
                  <Button
                    type="button"
                    onClick={handleHeroPrimaryAction}
                    className="rounded-[22px] bg-ink/92 px-5 py-3 text-sm font-[700] shadow-[0_16px_34px_rgba(29,42,56,0.12)] hover:bg-ink"
                  >
                    {heroPrimaryCtaLabel[locale]}
                  </Button>
                </div>
              </div>

              <div className="space-y-4 xl:max-w-[38rem] xl:justify-self-end">
                {heroTheses.map((item, index) => (
                  <div
                    key={item.title}
                    className={cn(
                      "welcome-reveal flex min-h-[128px] flex-col justify-center rounded-[28px] border bg-white/82 p-6 shadow-soft",
                      index === 2 ? "border-accent/20 bg-accent/[0.06]" : "border-white/60",
                      heroVisible && "is-visible",
                    )}
                    style={{ transitionDelay: `${410 + index * 90}ms` }}
                  >
                    <div className="text-[0.68rem] uppercase tracking-[0.24em] text-coral">{item.eyebrow}</div>
                    <div className="mt-3 text-lg font-[700] leading-7 tracking-[-0.025em] text-ink">{item.title}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div
          className="absolute bottom-32 left-1/2 z-20 md:bottom-36 lg:bottom-40"
          style={{ transform: "translateX(-50%)" }}
        >
          <div
            className={cn(
              "welcome-reveal rounded-[42px] bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.26),rgba(255,255,255,0.09)_52%,transparent_80%)] px-6 py-4 shadow-[0_18px_42px_rgba(255,255,255,0.08)] backdrop-blur-[2px] md:px-7 md:py-5",
              heroVisible && "is-visible",
            )}
            style={{ transitionDelay: "610ms" }}
          >
            <ConvergingPathsScrollIndicator
              activeMessageIndex={welcomeScrollIndicatorConfig.activeMessageIndex}
              ariaLabel={heroScrollCueAriaLabel[locale]}
              color={welcomeScrollIndicatorConfig.color}
              height={welcomeScrollIndicatorConfig.height}
              intensity={welcomeScrollIndicatorConfig.intensity}
              messages={welcomeScrollIndicatorMessages[locale]}
              opacity={welcomeScrollIndicatorConfig.opacity}
              targetId={HERO_PRIMARY_SCROLL_TARGET_ID}
              targetRef={onboardingSectionRef}
              timings={welcomeScrollIndicatorConfig.timings}
              width={welcomeScrollIndicatorConfig.width}
            />
          </div>
        </div>

        <WelcomeSignInModal
          account={signInView.account}
          canSubmit={signInView.canSubmit}
          copy={signInView.copy}
          error={signInView.error}
          isOpen={signInView.isOpen}
          isSubmitting={signInView.isSubmitting}
          onClose={signInView.close}
          onSubmit={signInView.submit}
          setAccount={signInView.setAccount}
        />
      </section>

      <section
        id={HERO_PRIMARY_SCROLL_TARGET_ID}
        ref={onboardingSectionRef}
        className="welcome-shell welcome-screen welcome-screen--secondary relative px-6 py-10 lg:px-8 lg:py-12"
      >
        <div className="welcome-shell__noise" />

        <div className="relative z-10 mx-auto max-w-[980px]">
          <div className={cn("welcome-reveal text-center", wizardVisible && "is-visible")}>
            <div className="text-xs uppercase tracking-[0.28em] text-coral">{tr("Mini-onboarding")}</div>
            <h2 className="mt-4 text-3xl font-[700] tracking-[-0.035em] text-ink lg:text-[3rem]">{tr("Answer 3 short questions and build the first lesson.")}</h2>
            <p className="mx-auto mt-4 max-w-[40rem] text-base leading-7 text-slate-600">
              {tr("A short lesson comes first. Registration and payment can wait until the value feels obvious.")}
            </p>
          </div>

          <div className={cn("welcome-reveal mt-8 rounded-[34px] border border-white/65 bg-white/82 p-5 shadow-soft backdrop-blur md:p-6", wizardVisible && "is-visible")} style={{ transitionDelay: "120ms" }}>
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-[0.24em] text-coral">{tr("Mini-onboarding")}</div>
                <div className="mt-2 text-2xl font-[700] tracking-[-0.03em] text-ink">{activeStepTitle}</div>
              </div>
              <div className="rounded-2xl bg-sand/80 px-4 py-3 text-right">
                <div className="text-xs uppercase tracking-[0.14em] text-slate-500">{tr("Step")}</div>
                <div className="mt-1 text-lg font-[700] tracking-[-0.02em] text-ink">{step + 1}/3</div>
              </div>
            </div>

            <div className="mt-4 h-2 rounded-full bg-sand/80">
              <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${((step + 1) / 3) * 100}%` }} />
            </div>

            <div className="mt-5 text-sm leading-6 text-slate-600">{activeStepDescription}</div>

            <div key={step} className="mt-6 onboarding-step-panel">
              {step === 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {directionCards.map((card, index) => {
                    const active = selectedDirections.includes(card.id);
                    const disabled = !active && selectionLimitReached;

                    return (
                      <button
                        key={card.id}
                        type="button"
                        onClick={() => handleDirectionToggle(card.id)}
                        disabled={disabled}
                        className={cn(
                          "welcome-reveal rounded-[24px] border px-4 py-4 text-left transition-all",
                          wizardVisible && "is-visible",
                          active
                            ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.95))] shadow-soft"
                            : "border-white/60 bg-[#fffaf4] hover:-translate-y-0.5 hover:bg-white",
                          disabled && "cursor-not-allowed opacity-45 hover:translate-y-0",
                        )}
                        style={{ transitionDelay: `${180 + index * 55}ms` }}
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
                  {painOptions.map((option, index) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setPainPoint(option.value)}
                      className={cn(
                        "welcome-reveal w-full rounded-[24px] border px-4 py-4 text-left transition-all",
                        wizardVisible && "is-visible",
                        painPoint === option.value
                          ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.96))] shadow-soft"
                          : "border-white/60 bg-[#fffaf4] hover:bg-white",
                      )}
                      style={{ transitionDelay: `${180 + index * 70}ms` }}
                    >
                      <div className="text-base font-semibold text-ink">{tr(option.title)}</div>
                      <div className="mt-2 text-sm leading-6 text-slate-600">{tr(option.subtitle)}</div>
                    </button>
                  ))}
                </div>
              ) : null}

              {step === 2 ? (
                <div className="space-y-3">
                  {lessonToneOptions.map((option, index) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setLessonTone(option.value)}
                      className={cn(
                        "welcome-reveal w-full rounded-[24px] border px-4 py-4 text-left transition-all",
                        wizardVisible && "is-visible",
                        lessonTone === option.value
                          ? "border-accent/45 bg-[linear-gradient(180deg,rgba(15,118,110,0.08),rgba(255,255,255,0.96))] shadow-soft"
                          : "border-white/60 bg-[#fffaf4] hover:bg-white",
                      )}
                      style={{ transitionDelay: `${180 + index * 70}ms` }}
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
          </div>
        </div>
      </section>
    </div>
  );
}

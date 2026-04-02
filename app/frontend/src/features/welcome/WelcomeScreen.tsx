import { useEffect, useRef, useState } from "react";
import { useLocale } from "../../shared/i18n/useLocale";
import { ConvergingPathsScrollIndicator } from "../../shared/ui/ConvergingPathsScrollIndicator";
import { Button } from "../../shared/ui/Button";
import { cn } from "../../shared/utils/cn";
import { WelcomeProofLesson } from "./WelcomeProofLesson";
import { WelcomePremiumHeader } from "./WelcomePremiumHeader";
import { WelcomeSignInModal } from "./WelcomeSignInModal";
import { useWelcomeSignIn } from "./useWelcomeSignIn";
import {
  welcomeScrollIndicatorConfig,
  welcomeScrollIndicatorMessages,
} from "./welcomeScrollIndicator";

const HERO_PRIMARY_SCROLL_TARGET_ID = "welcome-mini-onboarding";
const HERO_WHEEL_TRIGGER_THRESHOLD = 72;
const HERO_TRACKPAD_TRIGGER_THRESHOLD = 148;
const HERO_WHEEL_DEBOUNCE_MS = 180;
const HERO_TRACKPAD_DEBOUNCE_MS = 260;
const HERO_WHEEL_COOLDOWN_MS = 1100;
const HERO_WHEEL_MAX_SCROLL_Y = 56;
const HERO_RETURN_MIN_SCROLL_Y = 84;
const HERO_RETURN_TOP_TOLERANCE = 112;
const HERO_TRACKPAD_MICRO_SCROLL_THRESHOLD = 6;
const HERO_TRACKPAD_EVENT_DELTA_MAX = 32;

const heroPrimaryCtaLabel = {
  ru: "Просто попробовать урок",
  en: "Build the first lesson",
} as const;

const heroScrollCueAriaLabel = {
  ru: "Прокрутите, чтобы увидеть, как Verba собирает обучение в одну систему",
  en: "Scroll to see how Verba brings learning into one system",
} as const;

export function WelcomeScreen() {
  const [scrollY, setScrollY] = useState(0);
  const [heroVisible, setHeroVisible] = useState(false);
  const [wizardVisible, setWizardVisible] = useState(false);
  const { locale, setLocale, tr } = useLocale();
  const signInView = useWelcomeSignIn(locale);
  const localeOptions = [
    { value: "ru" as const, label: "RU", flagClass: "locale-flag--ru" },
    { value: "en" as const, label: "EN", flagClass: "locale-flag--en" },
  ];
  const heroSectionRef = useRef<HTMLElement | null>(null);
  const onboardingSectionRef = useRef<HTMLElement | null>(null);
  const heroWheelAccumulatedDeltaRef = useRef(0);
  const heroWheelDirectionRef = useRef<1 | -1 | 0>(0);
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
    const onboardingNode = onboardingSectionRef.current;
    if (!heroNode || !onboardingNode) {
      return;
    }

    const resetWheelIntent = () => {
      heroWheelAccumulatedDeltaRef.current = 0;
      heroWheelDirectionRef.current = 0;

      if (heroWheelDebounceRef.current !== null) {
        window.clearTimeout(heroWheelDebounceRef.current);
        heroWheelDebounceRef.current = null;
      }
    };

    const scrollToViewportTop = (top: number) => {
      window.scrollTo({
        top: Math.max(0, top),
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
      });
    };

    const getSectionViewportTop = (node: HTMLElement) =>
      window.scrollY + node.getBoundingClientRect().top;

    const triggerHeroSectionAdvance = () => {
      scrollToViewportTop(getSectionViewportTop(onboardingNode));
    };

    const triggerHeroSectionReturn = () => {
      scrollToViewportTop(getSectionViewportTop(heroNode));
    };

    const handleWheel = (event: WheelEvent) => {
      if (event.ctrlKey || Math.abs(event.deltaY) <= Math.abs(event.deltaX) || event.deltaY === 0) {
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
      const onboardingRect = onboardingNode.getBoundingClientRect();
      const heroIsPrimaryViewport =
        window.scrollY <= HERO_WHEEL_MAX_SCROLL_Y &&
        heroRect.top <= 8 &&
        heroRect.bottom >= window.innerHeight * 0.55;
      const onboardingIsPrimaryViewport =
        window.scrollY >= HERO_RETURN_MIN_SCROLL_Y &&
        onboardingRect.top <= HERO_RETURN_TOP_TOLERANCE &&
        onboardingRect.bottom >= window.innerHeight * 0.45;
      const direction = event.deltaY > 0 ? 1 : -1;
      const movingDownFromHero = direction === 1 && heroIsPrimaryViewport;
      const movingUpFromOnboarding = direction === -1 && onboardingIsPrimaryViewport;

      if (!movingDownFromHero && !movingUpFromOnboarding) {
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
        ? Math.max(0, Math.abs(event.deltaY) - HERO_TRACKPAD_MICRO_SCROLL_THRESHOLD) * 0.9
        : Math.abs(event.deltaY);

      if (heroWheelDirectionRef.current !== direction) {
        heroWheelAccumulatedDeltaRef.current = 0;
        heroWheelDirectionRef.current = direction;
      }

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
      if (movingDownFromHero) {
        triggerHeroSectionAdvance();
        return;
      }

      triggerHeroSectionReturn();
    };

    window.addEventListener("wheel", handleWheel, { passive: false });

    return () => {
      window.removeEventListener("wheel", handleWheel);
      resetWheelIntent();
    };
  }, []);

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

    if (!targetSection) {
      return;
    }

    window.scrollTo({
      top: window.scrollY + targetSection.getBoundingClientRect().top,
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
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
            <div className="grid w-full gap-8 xl:-translate-y-14 xl:grid-cols-[minmax(0,1.04fr)_minmax(360px,0.82fr)] xl:items-center 2xl:-translate-y-16">
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
        <WelcomeProofLesson isVisible={wizardVisible} locale={locale} />
      </section>
    </div>
  );
}

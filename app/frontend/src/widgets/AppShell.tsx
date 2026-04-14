import { useEffect } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { routes } from "../shared/constants/routes";
import { readStoredActiveUserId } from "../shared/auth/active-user";
import { useLocale } from "../shared/i18n/useLocale";
import { useAppStore } from "../shared/store/app-store";
import { cn } from "../shared/utils/cn";
import { LivingBackgroundSystem } from "./living-background/LivingBackgroundSystem";
import { LivingDepthSection } from "./living-background/LivingDepthSection";
import { getLivingDepthRouteSectionId } from "./living-background/livingBackgroundConfig";
import { AppTopRail } from "./navigation/AppTopRail";
import { JourneyReentryPrompt } from "./navigation/JourneyReentryPrompt";

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const isWelcomeRoute = location.pathname === routes.welcome;
  const isWelcomeClassicRoute = location.pathname === routes.welcomeClassic;
  const isOnboardingRoute = location.pathname === routes.onboarding;
  const routeSectionId = getLivingDepthRouteSectionId(location.pathname);
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const isBootstrapping = useAppStore((state) => state.isBootstrapping);
  const bootstrapError = useAppStore((state) => state.bootstrapError);
  const needsOnboarding = useAppStore((state) => state.needsOnboarding);
  const resumeLessonRun = useAppStore((state) => state.resumeLessonRun);
  const startTodayDailyLoop = useAppStore((state) => state.startTodayDailyLoop);
  const hasStoredActiveUser = Boolean(readStoredActiveUserId());
  const shouldShowGuestEntry = needsOnboarding || !hasStoredActiveUser;
  const { locale, setLocale, tr, formatRecommendationGoal } = useLocale();
  const localeOptions = [
    { value: "ru" as const, label: "RU", flagClass: "locale-flag--ru" },
    { value: "en" as const, label: "EN", flagClass: "locale-flag--en" },
  ];

  const recommendationGoal = dashboard
    ? formatRecommendationGoal({
        lessonType: dashboard.recommendation.lessonType,
        focusArea: dashboard.recommendation.focusArea,
        weakSpotTitles: dashboard.weakSpots.map((spot) => spot.title),
        dueVocabularyCount: dashboard.studyLoop?.vocabularySummary.dueCount ?? 0,
        professionTrack: dashboard.profile.professionTrack,
      })
    : null;

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  async function handleResumeRoute() {
    await resumeLessonRun();
    navigate(routes.lessonRunner);
  }

  async function handleStartTodayRoute() {
    await startTodayDailyLoop();
    navigate(routes.lessonRunner);
  }

  function handleOpenDashboard() {
    navigate(routes.dashboard);
  }

  if (shouldShowGuestEntry && !isOnboardingRoute && !isWelcomeRoute && !isWelcomeClassicRoute) {
    return <Navigate to={routes.welcome} replace />;
  }

  if (!shouldShowGuestEntry && (isOnboardingRoute || isWelcomeRoute || isWelcomeClassicRoute)) {
    return <Navigate to={routes.dashboard} replace />;
  }

  if (shouldShowGuestEntry && (isOnboardingRoute || isWelcomeRoute || isWelcomeClassicRoute)) {
    return (
      <div className="onboarding-layout living-depth-shell">
        <LivingBackgroundSystem routeSectionId={routeSectionId} />
        <div className="onboarding-layout__orb onboarding-layout__orb--left" />
        <div className="onboarding-layout__orb onboarding-layout__orb--right" />
        {!isWelcomeRoute && !isWelcomeClassicRoute ? (
          <div className="absolute right-4 top-4 z-20 lg:right-6 lg:top-6">
            <div className="flex rounded-full border border-white/60 bg-white/80 p-1 shadow-soft backdrop-blur">
              {localeOptions.map((targetLocale) => (
                <button
                  key={targetLocale.value}
                  type="button"
                  onClick={() => setLocale(targetLocale.value)}
                  className={cn(
                    "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-colors",
                    locale === targetLocale.value ? "bg-accent text-white" : "text-slate-600 hover:text-ink",
                  )}
                >
                  <span className={cn("locale-flag", targetLocale.flagClass)} aria-hidden="true">
                    {targetLocale.value === "en" ? <span className="locale-flag__canton" /> : null}
                  </span>
                  <span>{tr(targetLocale.label)}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
        <LivingDepthSection
          id={routeSectionId}
          fallback
          as="main"
          className="relative z-10 mx-auto w-full max-w-[1500px] px-4 py-16 lg:px-6 lg:py-10"
        >
          <Outlet />
        </LivingDepthSection>
      </div>
    );
  }

  return (
    <div className="living-depth-shell min-h-screen px-4 py-4 lg:px-6">
      <LivingBackgroundSystem routeSectionId={routeSectionId} />
      <div className="relative z-10 mx-auto max-w-[1480px]">
        <AppTopRail
          bootstrapError={bootstrapError}
          dashboard={dashboard}
          isBootstrapping={isBootstrapping}
          locale={locale}
          localeOptions={localeOptions}
          recommendationGoal={recommendationGoal}
          setLocale={setLocale}
          tr={tr}
        />
        <JourneyReentryPrompt
          dashboard={dashboard}
          pathname={location.pathname}
          onOpenDashboard={handleOpenDashboard}
          onResumeRoute={handleResumeRoute}
          onStartTodayRoute={handleStartTodayRoute}
          tr={tr}
        />

        <LivingDepthSection
          id={routeSectionId}
          fallback
          as="main"
          className="mt-4 pb-10"
        >
          <Outlet />
        </LivingDepthSection>
      </div>
    </div>
  );
}

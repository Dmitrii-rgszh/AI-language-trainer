import { useEffect, useRef } from "react";
import { Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { apiClient } from "../shared/api/client";
import { routes } from "../shared/constants/routes";
import { readStoredActiveUserId } from "../shared/auth/active-user";
import { useLocale } from "../shared/i18n/useLocale";
import { describeRouteDayShape } from "../shared/journey/route-day-shape";
import { resolveRouteEntryDecision } from "../shared/journey/route-entry-orchestration";
import { buildRoutePriorityView, buildRouteProtectionView } from "../shared/journey/route-priority";
import { useAppStore } from "../shared/store/app-store";
import { cn } from "../shared/utils/cn";
import { LivingBackgroundSystem } from "./living-background/LivingBackgroundSystem";
import { LivingDepthSection } from "./living-background/LivingDepthSection";
import { getLivingDepthRouteSectionId } from "./living-background/livingBackgroundConfig";
import { AppTopRail } from "./navigation/AppTopRail";
import { JourneyReentryPrompt } from "./navigation/JourneyReentryPrompt";
import { RouteEntryNotice } from "./navigation/RouteEntryNotice";

function mapCurrentSurfaceLabel(pathname: string, tr: (value: string) => string): string | null {
  return (
    {
      [routes.dashboard]: tr("dashboard route"),
      [routes.dailyLoop]: tr("daily route"),
      [routes.lessonRunner]: tr("guided lesson"),
      [routes.lessonResults]: tr("lesson results"),
      [routes.activity]: tr("activity route"),
      [routes.listening]: tr("listening support"),
      [routes.grammar]: tr("grammar support"),
      [routes.vocabulary]: tr("vocabulary support"),
      [routes.reading]: tr("reading support"),
      [routes.speaking]: tr("speaking support"),
      [routes.pronunciation]: tr("pronunciation support"),
      [routes.writing]: tr("writing support"),
      [routes.profession]: tr("professional support"),
      [routes.progress]: tr("progress route"),
    }[pathname] ?? null
  );
}

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const hasAppliedEntryOrchestrationRef = useRef(false);
  const lastRecordedRouteEntryRef = useRef<string | null>(null);
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
  const routePriorityView = buildRoutePriorityView(dashboard ?? null, tr);
  const routeProtectionView = buildRouteProtectionView(dashboard ?? null, tr);
  const routeRecoveryMemory = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = dashboard?.journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = dashboard?.journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const routeDayShape = dashboard?.dailyLoopPlan
    ? describeRouteDayShape(dashboard.dailyLoopPlan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr)
    : null;
  const locationState = (location.state ?? null) as {
    routeEntryReason?: string;
    routeEntrySource?: string;
    routeEntryFollowUpLabel?: string;
    routeEntryStageLabel?: string;
    routeEntryExpansionStageLabel?: string;
    skipRouteEntryOrchestrationOnce?: boolean;
  } | null;
  const routeEntryReason = locationState?.routeEntryReason ?? null;
  const routeEntrySource = locationState?.routeEntrySource ?? null;
  const routeEntryFollowUpLabel = locationState?.routeEntryFollowUpLabel ?? null;
  const routeEntryStageLabel = locationState?.routeEntryStageLabel ?? null;
  const routeEntryExpansionStageLabel = locationState?.routeEntryExpansionStageLabel ?? null;
  const routeEntryCurrentLabel = mapCurrentSurfaceLabel(location.pathname, tr);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  useEffect(() => {
    if (isBootstrapping || !dashboard || location.pathname !== routes.dashboard || hasAppliedEntryOrchestrationRef.current) {
      return;
    }

    if (locationState?.skipRouteEntryOrchestrationOnce) {
      hasAppliedEntryOrchestrationRef.current = true;
      return;
    }

    const entryDecision = resolveRouteEntryDecision(dashboard, tr);
    if (!entryDecision || entryDecision.route === routes.dashboard) {
      hasAppliedEntryOrchestrationRef.current = true;
      return;
    }

    hasAppliedEntryOrchestrationRef.current = true;
    navigate(entryDecision.route, {
      replace: true,
      state: {
        routeEntryReason: entryDecision.reason,
        routeEntrySource: "shell_reentry_orchestration",
        routeEntryFollowUpLabel: entryDecision.followUpLabel ?? null,
        routeEntryStageLabel: entryDecision.stageLabel ?? null,
        routeEntryExpansionStageLabel: entryDecision.expansionStageLabel ?? null,
      },
    });
  }, [dashboard, isBootstrapping, location.pathname, locationState?.skipRouteEntryOrchestrationOnce, navigate, tr]);

  useEffect(() => {
    if (isBootstrapping || !dashboard) {
      return;
    }

    const trackableRoutes = new Set<string>([
      routes.dashboard,
      routes.dailyLoop,
      routes.lessonRunner,
      routes.activity,
      routes.progress,
      routes.listening,
      routes.grammar,
      routes.vocabulary,
      routes.reading,
      routes.speaking,
      routes.pronunciation,
      routes.writing,
      routes.profession,
    ]);
    if (!trackableRoutes.has(location.pathname)) {
      return;
    }

    const source =
      routeEntrySource === "shell_reentry_orchestration"
        ? "smart_reentry"
        : "surface_visit";
    const entryKey = [
      location.pathname,
      source,
      dashboard.journeyState?.updatedAt ?? "stable",
      dashboard.dailyLoopPlan?.id ?? "no-plan",
    ].join("|");
    if (lastRecordedRouteEntryRef.current === entryKey) {
      return;
    }

    lastRecordedRouteEntryRef.current = entryKey;
    void apiClient.registerRouteEntry({
      route: location.pathname,
      source,
    }).catch(() => {
      // Ignore logging errors to avoid interrupting navigation.
    });
  }, [
    dashboard,
    isBootstrapping,
    location.pathname,
    routeEntrySource,
  ]);

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

  function handleDismissRouteEntryNotice() {
    navigate(`${location.pathname}${location.search}`, {
      replace: true,
      state: null,
    });
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
          routeProtectionDeferredLabel={routeProtectionView.deferredLabel}
          routeProtectionReason={routeProtectionView.deferredReason}
          routeSoftLockActive={routeProtectionView.isSoftLockActive}
          routeDayShapeCompactnessLabel={routeDayShape?.compactnessLabel ?? null}
          routeDayShapeSequenceLabel={routeDayShape?.sequenceLabel ?? null}
          routeDayShapeSummary={routeDayShape?.summary ?? null}
          routeDayShapeTitle={routeDayShape?.title ?? null}
          routePriorityPrimaryRoute={routePriorityView.primaryRoute}
          routePriorityStageLabel={routePriorityView.expansionStageLabel ?? routePriorityView.reopenStageLabel ?? null}
          routePriorityMode={routePriorityView.mode}
          routePrioritySummary={routePriorityView.summary}
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
        {routeEntryReason ? (
          <RouteEntryNotice
            reason={routeEntryReason}
            currentLabel={routeEntryCurrentLabel}
            followUpLabel={routeEntryFollowUpLabel}
            stageLabel={routeEntryExpansionStageLabel ?? routeEntryStageLabel}
            sourceLabel={
              routeEntrySource === "shell_reentry_orchestration"
                ? tr("smart re-entry")
                : routeEntrySource === "proof_lesson_completion"
                  ? tr("proof-lesson handoff")
                : routeEntrySource === "onboarding_completion"
                  ? tr("onboarding handoff")
                : routeEntrySource === "dashboard_route_launch"
                  ? tr("route launch")
                : routeEntrySource === "task_driven_handoff"
                  ? tr("task-driven handoff")
                : routeEntrySource === "lesson_completion"
                  ? tr("lesson completion")
                : routeEntrySource === "lesson_discard"
                  ? tr("draft return")
                : routeEntrySource === "results_follow_up"
                  ? tr("results follow-up")
                : routeEntrySource === "results_to_dashboard"
                  ? tr("results handoff")
                : routeEntrySource === "support_step_follow_up"
                  ? tr("support step follow-up")
                : routeEntrySource
            }
            onDismiss={handleDismissRouteEntryNotice}
            tr={tr}
          />
        ) : null}

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

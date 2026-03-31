import { useEffect } from "react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import { routes } from "../shared/constants/routes";
import { navigationItems } from "../shared/constants/navigation";
import { useLocale } from "../shared/i18n/useLocale";
import { useAppStore } from "../shared/store/app-store";
import { cn } from "../shared/utils/cn";
import { ProgressBar } from "../shared/ui/ProgressBar";

export function AppShell() {
  const location = useLocation();
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const isBootstrapping = useAppStore((state) => state.isBootstrapping);
  const bootstrapError = useAppStore((state) => state.bootstrapError);
  const needsOnboarding = useAppStore((state) => state.needsOnboarding);
  const { locale, setLocale, tr, formatRecommendationGoal } = useLocale();

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

  if (needsOnboarding && location.pathname !== routes.onboarding) {
    return <Navigate to={routes.onboarding} replace />;
  }

  return (
    <div className="min-h-screen px-4 py-4 lg:px-6">
      <div className="mx-auto grid max-w-[1440px] gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="glass-panel rounded-[32px] border border-white/60 p-5 shadow-soft">
          <div className="rounded-[24px] bg-ink px-4 py-5 text-white">
            <div className="text-xs uppercase tracking-[0.26em] text-teal-200">{tr("AI English Trainer Pro")}</div>
            <div className="mt-3 text-2xl font-semibold leading-tight">
              {tr("Unified English hub with a professional track")}
            </div>
            <div className="mt-4 text-sm text-slate-200">
              {tr("Personal English workspace for focused daily progress.")}
            </div>
          </div>

          <nav className="mt-5 space-y-2">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "block rounded-2xl px-4 py-3 text-sm font-medium transition-colors",
                    isActive ? "bg-accent text-white" : "bg-white/60 text-slate-700 hover:bg-white",
                  )
                }
              >
                {tr(item.label)}
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="space-y-4">
          <header className="glass-panel rounded-[32px] border border-white/60 px-5 py-4 shadow-soft">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="text-xs uppercase tracking-[0.26em] text-coral">{tr("Today")}</div>
                <div className="mt-1 text-xl font-semibold text-ink">
                  {needsOnboarding
                    ? tr("Complete onboarding")
                    : dashboard?.recommendation.title
                      ? tr(dashboard.recommendation.title)
                      : tr("Loading dashboard")}
                </div>
                <div className="mt-1 text-sm text-slate-600">
                  {needsOnboarding
                    ? tr("Finish onboarding to unlock your personal lesson plan.")
                    : recommendationGoal ?? tr("Loading your learning plan.")}
                </div>
              </div>

              <div className="min-w-[280px] rounded-[24px] bg-white/70 px-4 py-3">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
                    {tr("Interface language")}
                  </span>
                  <div className="flex rounded-full bg-sand/90 p-1">
                    {(["ru", "en"] as const).map((targetLocale) => (
                      <button
                        key={targetLocale}
                        type="button"
                        onClick={() => setLocale(targetLocale)}
                        className={cn(
                          "rounded-full px-3 py-1 text-xs font-semibold transition-colors",
                          locale === targetLocale ? "bg-accent text-white" : "text-slate-600 hover:text-ink",
                        )}
                      >
                        {tr(targetLocale.toUpperCase())}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm text-slate-600">
                  <span>{tr("Daily progress")}</span>
                  <span>
                    {dashboard?.progress.minutesCompletedToday ?? 0}/{dashboard?.progress.dailyGoalMinutes ?? 25} min
                  </span>
                </div>
                <div className="mt-3">
                  <ProgressBar
                    value={
                      dashboard
                        ? (dashboard.progress.minutesCompletedToday / dashboard.progress.dailyGoalMinutes) * 100
                        : 0
                    }
                  />
                </div>
                <div className="mt-3 text-xs text-slate-500">
                  {bootstrapError
                    ? `${tr("Backend unavailable")}: ${bootstrapError}`
                    : needsOnboarding
                      ? tr("Create your profile to unlock the first dashboard and lesson track.")
                    : isBootstrapping
                      ? tr("Loading your learning workspace...")
                      : `${tr("Current streak")}: ${dashboard?.progress.streak ?? 0}`}
                </div>
              </div>
            </div>
          </header>

          <main>
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}

import { NavLink } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { navigationItems } from "../../shared/constants/navigation";
import type { AppLocale } from "../../shared/i18n/locale";
import type { DashboardData } from "../../shared/types/app-data";
import { BrandLogo } from "../../shared/ui/BrandLogo";
import { ProgressBar } from "../../shared/ui/ProgressBar";
import { cn } from "../../shared/utils/cn";

type LocaleOption = {
  value: AppLocale;
  label: string;
  flagClass: string;
};

type AppTopRailProps = {
  bootstrapError: string | null;
  dashboard: DashboardData | null;
  isBootstrapping: boolean;
  locale: AppLocale;
  localeOptions: LocaleOption[];
  recommendationGoal: string | null;
  setLocale: (locale: AppLocale) => void;
  tr: (value: string) => string;
};

const topRailNavigationItems = navigationItems.filter((item) => item.to !== routes.onboarding);

export function AppTopRail({
  bootstrapError,
  dashboard,
  isBootstrapping,
  locale,
  localeOptions,
  recommendationGoal,
  setLocale,
  tr,
}: AppTopRailProps) {
  const dailyGoalMinutes = dashboard?.progress.dailyGoalMinutes ?? 25;
  const minutesCompletedToday = dashboard?.progress.minutesCompletedToday ?? 0;
  const dailyProgressValue = dailyGoalMinutes > 0 ? (minutesCompletedToday / dailyGoalMinutes) * 100 : 0;
  const streak = dashboard?.progress.streak ?? 0;
  const focusTitle = dashboard?.recommendation.title
    ? tr(dashboard.recommendation.title)
    : tr("Loading dashboard");
  const focusDescription = bootstrapError
    ? `${tr("Backend unavailable")}: ${bootstrapError}`
    : recommendationGoal ??
      (isBootstrapping
        ? tr("Loading your learning workspace...")
        : tr("Personal English workspace for focused daily progress."));

  return (
    <div className="app-top-rail">
      <div className="app-top-rail__frame glass-panel rounded-[34px] border border-white/70 shadow-soft">
        <div className="relative z-[1] flex flex-col gap-4 p-3 md:p-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div className="min-w-0 flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="inline-flex shrink-0 rounded-[24px] bg-white/94 px-4 py-3 shadow-[0_12px_30px_rgba(148,163,184,0.22)]">
                <BrandLogo className="w-[118px] lg:w-[128px]" />
              </div>

              <div className="min-w-0">
                <div className="text-[0.68rem] uppercase tracking-[0.22em] text-coral">{tr("Today")}</div>
                <div className="mt-2 text-lg font-[700] tracking-[-0.025em] text-ink lg:text-[1.35rem]">{focusTitle}</div>
                <div className="mt-1 max-w-[42rem] text-sm leading-6 text-slate-600">{focusDescription}</div>
              </div>
            </div>

            <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch lg:justify-end">
              <div className="min-w-[236px] rounded-[24px] bg-[linear-gradient(145deg,rgba(255,255,255,0.82),rgba(244,250,249,0.74))] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
                <div className="flex items-center justify-between gap-4 text-sm text-slate-600">
                  <span>{tr("Daily progress")}</span>
                  <span className="font-[700] tracking-[-0.02em] text-ink">
                    {minutesCompletedToday}/{dailyGoalMinutes} min
                  </span>
                </div>
                <div className="mt-3">
                  <ProgressBar value={dailyProgressValue} />
                </div>
              </div>

              <div className="flex items-stretch gap-3">
                <div className="min-w-[108px] rounded-[24px] bg-[linear-gradient(145deg,rgba(255,250,245,0.86),rgba(255,243,232,0.72))] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]">
                  <div className="text-[0.68rem] uppercase tracking-[0.14em] text-coral">{tr("Current streak")}</div>
                  <div className="mt-2 text-xl font-[700] tracking-[-0.02em] text-ink">{streak}</div>
                </div>

                <div className="flex rounded-full border border-white/70 bg-white/86 p-1 shadow-[0_10px_24px_rgba(148,163,184,0.18)] backdrop-blur">
                  {localeOptions.map((targetLocale) => (
                    <button
                      key={targetLocale.value}
                      type="button"
                      onClick={() => setLocale(targetLocale.value)}
                      className={cn(
                        "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-[700] tracking-[-0.01em] transition-colors",
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
            </div>
          </div>

          <div className="app-top-rail__nav-shell rounded-[28px] border border-white/65 bg-white/54 px-2 py-2">
            <nav className="app-top-rail__nav-scroll flex items-center gap-2 overflow-x-auto px-1 py-1">
              {topRailNavigationItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "shrink-0 rounded-full border px-4 py-2.5 text-sm font-[650] tracking-[-0.01em] transition-all",
                      isActive
                        ? "border-transparent bg-ink text-white shadow-[0_12px_28px_rgba(29,42,56,0.22)]"
                        : "border-white/70 bg-white/72 text-slate-600 hover:bg-white hover:text-ink",
                    )
                  }
                >
                  {tr(item.label)}
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
}

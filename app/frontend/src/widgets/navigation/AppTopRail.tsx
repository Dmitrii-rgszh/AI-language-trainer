import { useEffect, useMemo, useRef, useState } from "react";
import { NavLink } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import type { AppLocale } from "../../shared/i18n/locale";
import type { DashboardData } from "../../shared/types/app-data";
import { BrandLogo } from "../../shared/ui/BrandLogo";
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
  routeDayShapeCompactnessLabel?: string | null;
  routeDayShapeSequenceLabel?: string | null;
  routeDayShapeSummary?: string | null;
  routeDayShapeTitle?: string | null;
  routePriorityPrimaryRoute?: string | null;
  routePriorityStageLabel?: string | null;
  routeProtectionReason?: string | null;
  routeSoftLockActive?: boolean;
  routePriorityMode?: string | null;
  setLocale: (locale: AppLocale) => void;
  tr: (value: string) => string;
  onOpenSettings: () => void;
  onSignOut: () => void;
};

const topRailNavigationItems = [
  { label: "Home", to: routes.dashboard },
  { label: "Route", to: routes.dailyLoop },
  { label: "Lesson", to: routes.lessonRunner },
  { label: "Practice", to: routes.activity },
  { label: "Progress", to: routes.progress },
] as const;

function SettingsIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M10.4 2.7h3.2l.5 2.1a7.8 7.8 0 0 1 1.7.7l1.9-1.1 2.2 2.2-1.1 1.9c.3.5.5 1.1.7 1.7l2.1.5v3.2l-2.1.5a7.8 7.8 0 0 1-.7 1.7l1.1 1.9-2.2 2.2-1.9-1.1c-.5.3-1.1.5-1.7.7l-.5 2.1h-3.2l-.5-2.1a7.8 7.8 0 0 1-1.7-.7l-1.9 1.1-2.2-2.2 1.1-1.9a7.8 7.8 0 0 1-.7-1.7l-2.1-.5v-3.2l2.1-.5c.1-.6.4-1.2.7-1.7L4.5 6.7l2.2-2.2 1.9 1.1c.5-.3 1.1-.5 1.7-.7z" />
      <circle cx="12" cy="12" r="3.1" />
    </svg>
  );
}

export function AppTopRail({
  bootstrapError,
  dashboard,
  isBootstrapping,
  locale,
  localeOptions,
  recommendationGoal,
  routeDayShapeCompactnessLabel,
  routeDayShapeSummary,
  routeDayShapeTitle,
  routePriorityPrimaryRoute,
  routePriorityStageLabel,
  routeProtectionReason,
  routeSoftLockActive,
  routePriorityMode,
  setLocale,
  tr,
  onOpenSettings,
  onSignOut,
}: AppTopRailProps) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!userMenuRef.current?.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsUserMenuOpen(false);
      }
    }

    window.addEventListener("mousedown", handlePointerDown);
    window.addEventListener("keydown", handleEscape);
    return () => {
      window.removeEventListener("mousedown", handlePointerDown);
      window.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const prioritizedRoutes: string[] =
    routePriorityPrimaryRoute &&
    routePriorityPrimaryRoute !== routes.dashboard &&
    routePriorityPrimaryRoute !== routes.dailyLoop &&
    routePriorityPrimaryRoute !== routes.lessonRunner
      ? routePriorityStageLabel === tr("Ready to widen") || routePriorityStageLabel === tr("First widening pass")
        ? [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress, routePriorityPrimaryRoute]
        : routePriorityStageLabel === tr("Stabilizing widening")
          ? [routes.dashboard, routes.dailyLoop, routePriorityPrimaryRoute, routes.activity, routes.progress]
          : routePriorityStageLabel === tr("Carry inside route")
            ? [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress, routePriorityPrimaryRoute]
            : routePriorityStageLabel === tr("Protect ritual")
              ? [routes.dashboard, routePriorityPrimaryRoute, routes.dailyLoop, routes.activity, routes.progress]
              : [routes.dashboard, routePriorityPrimaryRoute, routes.dailyLoop, routes.activity, routes.progress]
      : routePriorityMode === "checkpoint"
        ? [routes.dashboard, routes.progress, routes.dailyLoop, routes.activity]
        : routePriorityMode === "recovery"
          ? [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress]
          : routePriorityMode && routePriorityMode !== "lesson"
            ? [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress, routes.lessonRunner]
            : [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress];
  const deferredRoutes = topRailNavigationItems.filter((item) => !prioritizedRoutes.includes(item.to)).map((item) => item.to);
  const orderedNavigationItems = [
    ...topRailNavigationItems
      .filter((item) => prioritizedRoutes.includes(item.to))
      .sort((left, right) => prioritizedRoutes.indexOf(left.to) - prioritizedRoutes.indexOf(right.to)),
    ...topRailNavigationItems.filter((item) => !prioritizedRoutes.includes(item.to)),
  ];

  const userLabel = useMemo(() => {
    const rawName = dashboard?.profile.name?.trim();
    if (!rawName) {
      return "V";
    }
    return rawName.slice(0, 1).toUpperCase();
  }, [dashboard?.profile.name]);

  return (
    <div className="app-top-rail space-y-2">
      <div className="flex items-center justify-between gap-4 rounded-[28px] px-2 py-1">
        <NavLink to={routes.dashboard} className="welcome-premium-header__brand-object shrink-0">
          <BrandLogo className="w-[118px] lg:w-[128px]" />
        </NavLink>

        <div className="hidden min-w-0 flex-1 justify-center px-4 xl:flex">
          <nav className="flex w-full max-w-[760px] items-center justify-between gap-5">
            {orderedNavigationItems.map((item) => {
              const isDeferred = Boolean(routeSoftLockActive) && deferredRoutes.includes(item.to);

              if (isDeferred) {
                return (
                  <div
                    key={item.to}
                    className="flex-1 text-center text-base font-[650] tracking-[-0.01em] text-slate-400"
                    title={routeProtectionReason ?? undefined}
                    aria-disabled="true"
                  >
                    {tr(item.label)}
                  </div>
                );
              }

              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "flex-1 text-center text-[1.02rem] font-[650] tracking-[-0.015em] transition-colors",
                      isActive ? "text-ink" : "text-slate-500 hover:text-ink",
                    )
                  }
                >
                  {tr(item.label)}
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex rounded-full border border-white/70 bg-white/86 p-1 shadow-[0_10px_24px_rgba(148,163,184,0.14)] backdrop-blur">
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

          <div className="relative" ref={userMenuRef}>
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((current) => !current)}
              className="flex items-center gap-2 rounded-full border border-white/70 bg-white/88 px-2.5 py-1.5 text-slate-600 shadow-[0_10px_24px_rgba(148,163,184,0.14)] backdrop-blur hover:text-ink"
              aria-haspopup="menu"
              aria-expanded={isUserMenuOpen}
              aria-label={tr("Open settings")}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent text-xs font-[800] text-white">
                {userLabel}
              </span>
              <SettingsIcon />
            </button>

            {isUserMenuOpen ? (
              <div className="absolute right-0 top-[calc(100%+0.5rem)] z-50 min-w-[220px] rounded-[20px] border border-white/70 bg-white/95 p-2 shadow-[0_18px_42px_rgba(148,163,184,0.18)] backdrop-blur">
                <div className="px-3 py-2 text-xs uppercase tracking-[0.16em] text-slate-400">
                  {dashboard?.profile.name ?? tr("Profile settings")}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onOpenSettings();
                  }}
                  className="flex w-full items-center rounded-[14px] px-3 py-2 text-left text-sm font-[650] text-ink transition-colors hover:bg-slate-100/80"
                >
                  {tr("Open settings")}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    onSignOut();
                  }}
                  className="flex w-full items-center rounded-[14px] px-3 py-2 text-left text-sm font-[650] text-coral transition-colors hover:bg-rose-50"
                >
                  {tr("Sign out")}
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="xl:hidden">
        <nav className="flex items-center gap-5 overflow-x-auto px-1 py-1">
          {orderedNavigationItems.map((item) => {
            const isDeferred = Boolean(routeSoftLockActive) && deferredRoutes.includes(item.to);

            if (isDeferred) {
              return (
                <div
                  key={item.to}
                  className="shrink-0 text-sm font-[650] tracking-[-0.01em] text-slate-400"
                  title={routeProtectionReason ?? undefined}
                  aria-disabled="true"
                >
                  {tr(item.label)}
                </div>
              );
            }

            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "shrink-0 text-sm font-[650] tracking-[-0.01em] transition-colors",
                    isActive ? "text-ink" : "text-slate-500 hover:text-ink",
                  )
                }
              >
                {tr(item.label)}
              </NavLink>
            );
          })}
        </nav>
      </div>

    </div>
  );
}

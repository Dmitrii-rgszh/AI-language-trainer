import { routes } from "../constants/routes";
import type { DashboardData } from "../types/app-data";

export type RouteReentrySequenceState = {
  isActive: boolean;
  key: string | null;
  completedRoutes: string[];
  orderedRoutes: string[];
  nextRoute: string | null;
};

function isSequencedRecoveryPhase(phase: string | null | undefined): boolean {
  return phase === "skill_repair_cycle" || phase === "targeted_stabilization";
}

function mapFocusSkillToRoute(focusSkill: string | null | undefined): string | null {
  return focusSkill === "grammar"
    ? routes.grammar
    : focusSkill === "speaking"
      ? routes.speaking
      : focusSkill === "pronunciation"
        ? routes.pronunciation
        : focusSkill === "writing"
          ? routes.writing
          : focusSkill === "profession"
            ? routes.profession
            : focusSkill === "vocabulary"
              ? routes.vocabulary
              : null;
}

function buildOrderedSupportRoutes(focusRoute: string | null): string[] {
  const routeMap: Record<string, string[]> = {
    [routes.grammar]: [routes.grammar, routes.writing, routes.speaking, routes.vocabulary, routes.pronunciation],
    [routes.vocabulary]: [routes.vocabulary, routes.speaking, routes.writing, routes.grammar, routes.pronunciation],
    [routes.speaking]: [routes.speaking, routes.pronunciation, routes.writing, routes.vocabulary, routes.grammar],
    [routes.pronunciation]: [routes.pronunciation, routes.speaking, routes.vocabulary, routes.grammar, routes.writing],
    [routes.writing]: [routes.writing, routes.grammar, routes.vocabulary, routes.speaking, routes.pronunciation],
    [routes.profession]: [routes.profession, routes.speaking, routes.writing, routes.vocabulary, routes.grammar],
  };

  const ordered = focusRoute ? routeMap[focusRoute] ?? [focusRoute] : [];
  return [...new Set(ordered)];
}

export function readRouteReentrySequenceState(dashboard: DashboardData | null): RouteReentrySequenceState {
  const recoveryMemory = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const reentryProgress = dashboard?.journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const focusSkill = recoveryMemory?.focusSkill ?? dashboard?.journeyState?.currentFocusArea ?? null;
  const orderedRoutes = buildOrderedSupportRoutes(mapFocusSkillToRoute(focusSkill));
  const completedRoutes =
    reentryProgress?.completedRoutes?.filter((route) => orderedRoutes.includes(route)) ?? [];
  const nextRoute =
    reentryProgress?.nextRoute && orderedRoutes.includes(reentryProgress.nextRoute)
      ? reentryProgress.nextRoute
      : orderedRoutes.find((route) => !completedRoutes.includes(route)) ?? null;

  return {
    isActive: Boolean(
      orderedRoutes.length > 0 &&
        reentryProgress?.sequenceKey &&
        reentryProgress?.status !== "completed" &&
        isSequencedRecoveryPhase(recoveryMemory?.phase),
    ),
    key: reentryProgress?.sequenceKey ?? null,
    completedRoutes,
    orderedRoutes,
    nextRoute,
  };
}

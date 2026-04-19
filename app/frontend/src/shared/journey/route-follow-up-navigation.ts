import type { LearnerJourneyState } from "../types/app-data";

export type RouteFollowUpTransition = {
  route: string;
  reason: string;
  stageLabel?: string | null;
  nextLabel?: string | null;
};

export function resolveRouteFollowUpTransition(
  journeyState: LearnerJourneyState | null | undefined,
  currentRoute: string,
  tr: (value: string) => string,
): RouteFollowUpTransition | null {
  const followUp = journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  if (!followUp) {
    return null;
  }

  const currentTarget =
    typeof followUp.currentRoute === "string" && followUp.currentRoute.length > 0
      ? followUp.currentRoute
      : null;
  const followUpTarget =
    typeof followUp.followUpRoute === "string" && followUp.followUpRoute.length > 0
      ? followUp.followUpRoute
      : null;

  const targetRoute =
    currentTarget && currentTarget !== currentRoute
      ? currentTarget
      : followUpTarget && followUpTarget !== currentRoute
        ? followUpTarget
        : null;

  if (!targetRoute) {
    return null;
  }

  const summary =
    typeof followUp.summary === "string" && followUp.summary.length > 0
      ? followUp.summary
      : tr("The route has already advanced, so the strongest next move is to continue into the next connected surface.");

  const nextLabel =
    targetRoute === currentTarget
      ? followUp.currentLabel ?? null
      : followUp.followUpLabel ?? null;

  return {
    route: targetRoute,
    reason: summary,
    stageLabel: followUp.stageLabel ?? null,
    nextLabel,
  };
}

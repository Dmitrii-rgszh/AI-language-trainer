import { routes } from "../constants/routes";
import type { LearnerJourneyState } from "../types/app-data";
import { mapSupportRouteLabel } from "./route-entry-orchestration";
import { describeRitualWindow } from "./ritual-window";

export type RouteFollowUpTransition = {
  route: string;
  reason: string;
  stageLabel?: string | null;
  nextLabel?: string | null;
  carryLabel?: string | null;
};

export function resolveRouteFollowUpTransition(
  journeyState: LearnerJourneyState | null | undefined,
  currentRoute: string,
  tr: (value: string) => string,
): RouteFollowUpTransition | null {
  const followUp = journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  const ritualSignalMemory = journeyState?.strategySnapshot.ritualSignalMemory ?? null;
  const ritualWindow = describeRitualWindow(ritualSignalMemory, tr);
  if (!followUp) {
    if (
      ritualWindow?.stageKey === "protect_ritual" &&
      ritualSignalMemory?.activeRoute &&
      currentRoute === ritualSignalMemory.activeRoute
    ) {
      return {
        route: routes.dailyLoop,
        reason: tr(`The ritual pass has landed once, so the next move is to carry it into the connected daily route before it widens further.`),
        stageLabel: ritualWindow.title,
        nextLabel: tr("daily route"),
        carryLabel: tr("activity trail"),
      };
    }

    if (
      ritualWindow?.stageKey === "carry_inside_route" &&
      ritualSignalMemory?.activeRoute &&
      currentRoute === ritualSignalMemory.activeRoute
    ) {
      return {
        route: routes.dailyLoop,
        reason: tr(`This ritual signal is already stable enough to ride inside the broader route, so the daily route should take over again now.`),
        stageLabel: ritualWindow.title,
        nextLabel: tr("activity trail"),
        carryLabel: mapSupportRouteLabel(ritualSignalMemory.activeRoute, tr),
      };
    }

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
      : ritualWindow?.summary ??
        tr("The route has already advanced, so the strongest next move is to continue into the next connected surface.");

  const nextLabel =
    targetRoute === currentTarget
      ? followUp.followUpLabel ??
        (ritualWindow?.stageKey === "carry_inside_route" ? tr("activity trail") : null)
      : followUp.currentLabel ??
        (targetRoute === routes.dailyLoop && ritualSignalMemory?.activeRoute
          ? mapSupportRouteLabel(ritualSignalMemory.activeRoute, tr)
          : null);

  return {
    route: targetRoute,
    reason: summary,
    stageLabel: followUp.stageLabel ?? ritualWindow?.title ?? null,
    nextLabel,
    carryLabel:
      typeof followUp.carryLabel === "string" && followUp.carryLabel.length > 0
        ? followUp.carryLabel
        : null,
  };
}

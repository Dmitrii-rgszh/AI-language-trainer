import { routes } from "../constants/routes";
import { describeRitualWindow } from "./ritual-window";
import { resolveTaskDrivenInputSurface } from "./task-driven-input";
import type { DailyLoopPlan, DashboardData, LearnerJourneyState } from "../types/app-data";

export type RouteEntryDecision = {
  route: string;
  reason: string;
  followUpRoute?: string | null;
  followUpLabel?: string | null;
  stageLabel?: string | null;
  expansionStageLabel?: string | null;
};

export function mapSupportRouteLabel(route: string | null | undefined, tr: (value: string) => string): string | null {
  if (!route) {
    return null;
  }

  return (
    {
      [routes.grammar]: tr("grammar support"),
      [routes.vocabulary]: tr("vocabulary support"),
      [routes.listening]: tr("listening support"),
      [routes.reading]: tr("reading support"),
      [routes.speaking]: tr("speaking support"),
      [routes.pronunciation]: tr("pronunciation support"),
      [routes.writing]: tr("writing support"),
      [routes.profession]: tr("professional support"),
      [routes.dailyLoop]: tr("daily route"),
      [routes.lessonRunner]: tr("guided route"),
    }[route] ?? route
  );
}

export function mapReopenStageLabel(stage: string | null | undefined, tr: (value: string) => string): string | null {
  if (stage === "first_reopen") {
    return tr("First reopen");
  }
  if (stage === "settling_back_in") {
    return tr("Settling pass");
  }
  if (stage === "ready_to_expand") {
    return tr("Ready to widen");
  }
  return null;
}

export function mapExpansionStageLabel(stage: string | null | undefined, tr: (value: string) => string): string | null {
  if (stage === "first_widening_pass") {
    return tr("First widening pass");
  }
  if (stage === "stabilizing_widening") {
    return tr("Stabilizing widening");
  }
  if (stage === "ready_for_extension") {
    return tr("Ready for extension");
  }
  return null;
}

export function resolveRouteEntryDecision(
  dashboard: DashboardData | null,
  tr: (value: string) => string,
): RouteEntryDecision | null {
  if (!dashboard) {
    return null;
  }

  const plan = dashboard.dailyLoopPlan;
  const journeyState = dashboard.journeyState;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const ritualSignalMemory = journeyState?.strategySnapshot.ritualSignalMemory ?? null;
  const ritualWindow = describeRitualWindow(ritualSignalMemory, tr);
  const reopenStageLabel = mapReopenStageLabel(routeRecoveryMemory?.reopenStage, tr);
  const expansionStageLabel = mapExpansionStageLabel(routeRecoveryMemory?.decisionWindowStage, tr);
  const reopenSupportRoute =
    routeEntryMemory?.readyToReopenActiveNextRoute && routeEntryMemory.activeNextRoute
      ? routeEntryMemory.activeNextRoute
      : routeReentryProgress?.nextRoute ?? null;
  const reopenSupportLabel = mapSupportRouteLabel(reopenSupportRoute, tr);

  if (dashboard.resumeLesson) {
    return {
      route: routes.lessonRunner,
      reason: tr("An active guided route is already in progress, so re-entry should continue there first."),
      followUpRoute: routes.dailyLoop,
      followUpLabel: tr("daily route"),
    };
  }

  if (!plan || plan.completedAt) {
    return null;
  }

  const taskDrivenInput = resolveTaskDrivenInputSurface(plan, journeyState ?? null, tr);

  if (
    ritualWindow?.stageKey === "protect_ritual" &&
    ritualSignalMemory?.activeRoute &&
    routeRecoveryMemory?.phase !== "route_rebuild" &&
    routeRecoveryMemory?.phase !== "protected_return" &&
    !reopenSupportRoute
  ) {
    return {
      route: ritualSignalMemory.activeRoute,
      reason: tr(`This re-entry should start through ${mapSupportRouteLabel(ritualSignalMemory.activeRoute, tr) ?? tr("the ritual surface")} so the ritual signal lands once before the broader route takes over.`),
      followUpRoute: routes.dailyLoop,
      followUpLabel: tr("daily route"),
      stageLabel: ritualWindow.title,
      expansionStageLabel,
    };
  }

  if (routeRecoveryMemory?.phase === "support_reopen_arc" && reopenSupportRoute && reopenSupportLabel) {
    if (routeRecoveryMemory.reopenStage === "first_reopen") {
      return {
        route: reopenSupportRoute,
        reason: tr(`This return is the first controlled reopen, so ${reopenSupportLabel} should come first before the wider route starts moving again.`),
        followUpRoute: routes.dailyLoop,
        followUpLabel: tr("daily route"),
        stageLabel: reopenStageLabel,
        expansionStageLabel,
      };
    }

    if (routeRecoveryMemory.reopenStage === "settling_back_in") {
      return {
        route: reopenSupportRoute,
        reason: tr(`This return is still a settling pass, so ${reopenSupportLabel} should reopen first and then flow back into today's connected route.`),
        followUpRoute: routes.dailyLoop,
        followUpLabel: tr("daily route"),
        stageLabel: reopenStageLabel,
        expansionStageLabel,
      };
    }

    if (routeRecoveryMemory.reopenStage === "ready_to_expand") {
      return {
        route: routes.dailyLoop,
        reason:
          routeRecoveryMemory.decisionWindowStage === "first_widening_pass"
            ? tr(`The reopen arc is stable enough for a first widening pass, so re-entry should widen through the connected daily route while keeping ${reopenSupportLabel} quietly available.`)
            : routeRecoveryMemory.decisionWindowStage === "stabilizing_widening"
              ? tr(`The route has already completed its first wider pass, so re-entry should use one more stabilizing broader route before it extends further.`)
              : routeRecoveryMemory.decisionWindowStage === "ready_for_extension"
                ? tr(`The widening window has already held, so re-entry should keep the daily route in front and start extending beyond the protected reopen arc.`)
                : tr(`The reopen arc is stable enough now, so re-entry should widen through the connected daily route while keeping ${reopenSupportLabel} available inside it.`),
        followUpRoute:
          routeRecoveryMemory.decisionWindowStage === "ready_for_extension"
            ? routes.activity
            : reopenSupportRoute,
        followUpLabel:
          routeRecoveryMemory.decisionWindowStage === "ready_for_extension"
            ? tr("activity trail")
            : reopenSupportLabel,
        stageLabel: reopenStageLabel,
        expansionStageLabel,
      };
    }
  }

  if (
    routeReentryProgress?.nextRoute &&
    (routeRecoveryMemory?.phase === "skill_repair_cycle" ||
      routeRecoveryMemory?.phase === "targeted_stabilization" ||
      routeRecoveryMemory?.sessionShape === "focused_support")
  ) {
    if (
      routeEntryMemory?.activeNextRoute === routeReentryProgress.nextRoute &&
      (routeEntryMemory.activeNextRouteVisits ?? 0) >= 2 &&
      !routeEntryMemory.readyToReopenActiveNextRoute
    ) {
      return {
        route: routes.dailyLoop,
        reason: tr("The sequenced support step has already been reopened repeatedly, so re-entry should reset through the main route before trying the same support surface again."),
        followUpRoute: routeReentryProgress.nextRoute,
        followUpLabel: mapSupportRouteLabel(routeReentryProgress.nextRoute, tr),
      };
    }

    return {
      route: routeReentryProgress.nextRoute,
      reason: tr("This re-entry should reopen through the next sequenced support surface before widening again."),
      followUpRoute: routes.dailyLoop,
      followUpLabel: tr("daily route"),
    };
  }

  if (
    routeRecoveryMemory?.phase === "route_rebuild" ||
    routeRecoveryMemory?.phase === "protected_return" ||
    routeRecoveryMemory?.sessionShape === "gentle_restart" ||
    routeRecoveryMemory?.sessionShape === "protected_mix"
  ) {
    return {
      route: routes.dailyLoop,
      reason: tr("This re-entry should land in the protected main route before any side surface opens again."),
      followUpRoute: reopenSupportRoute,
      followUpLabel: reopenSupportLabel,
      stageLabel: reopenStageLabel,
      expansionStageLabel,
    };
  }

  if (ritualWindow?.stageKey === "carry_inside_route") {
    return {
      route: routes.dailyLoop,
      reason: tr(`The ritual signal is already stable enough to ride inside the broader route, so re-entry should land in today's daily route instead of restarting the ritual surface.`),
      followUpRoute: ritualSignalMemory?.activeRoute ?? null,
      followUpLabel: ritualSignalMemory?.activeRoute
        ? mapSupportRouteLabel(ritualSignalMemory.activeRoute, tr)
        : null,
      stageLabel: ritualWindow.title,
      expansionStageLabel,
    };
  }

  if (taskDrivenInput && !plan.lessonRunId) {
    return {
      route: taskDrivenInput.route,
      reason: tr(`Today's route is designed to begin through ${taskDrivenInput.label}, so re-entry should land there before the guided session opens.`),
      followUpRoute: routes.lessonRunner,
      followUpLabel: tr("guided route"),
      stageLabel: tr("Task-driven input"),
    };
  }

  return {
    route: routes.dailyLoop,
    reason: tr("The strongest re-entry point is today's connected route."),
    followUpRoute: reopenSupportRoute,
    followUpLabel: reopenSupportLabel,
    stageLabel: reopenStageLabel,
    expansionStageLabel,
  };
}

export function buildRouteFollowUpHint(
  dashboard: DashboardData | null,
  tr: (value: string) => string,
): string | null {
  if (!dashboard) {
    return null;
  }

  const persistedFollowUp = dashboard.journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  if (persistedFollowUp?.summary) {
    return persistedFollowUp.summary;
  }

  const decision = resolveRouteEntryDecision(dashboard, tr);
  const routeRecoveryMemory = dashboard.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeEntryMemory = dashboard.journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const reopenStageLabel = mapReopenStageLabel(routeRecoveryMemory?.reopenStage, tr);
  const expansionStageLabel = mapExpansionStageLabel(routeRecoveryMemory?.decisionWindowStage, tr);
  const reopenSupportLabel =
    routeEntryMemory?.readyToReopenActiveNextRoute && routeEntryMemory.activeNextRoute
      ? mapSupportRouteLabel(routeEntryMemory.activeNextRoute, tr)
      : null;

  if (!decision) {
    return null;
  }

  if (decision.followUpLabel && (reopenStageLabel || expansionStageLabel)) {
    return tr(
      `Stage: ${[reopenStageLabel, expansionStageLabel].filter(Boolean).join(" · ")}. After this step, the route should continue through ${decision.followUpLabel}.`,
    );
  }

  if (decision.followUpLabel) {
    return tr(`After this step, the route should continue through ${decision.followUpLabel}.`);
  }

  if (reopenSupportLabel && reopenStageLabel === tr("Ready to widen")) {
    return tr(`The route is widening again now, while keeping ${reopenSupportLabel} available inside the broader flow.`);
  }

  return null;
}

export function buildRouteFollowUpHintFromState(
  dailyLoopPlan: DailyLoopPlan | null,
  journeyState: LearnerJourneyState | null,
  tr: (value: string) => string,
): string | null {
  if (!journeyState) {
    return null;
  }

  const persistedFollowUp = journeyState.strategySnapshot.routeFollowUpMemory ?? null;
  if (persistedFollowUp?.summary) {
    return persistedFollowUp.summary;
  }

  return buildRouteFollowUpHint(
    ({
      dailyLoopPlan,
      journeyState,
      profile: {} as never,
      progress: {} as never,
      weakSpots: [],
      recommendation: {} as never,
      studyLoop: null,
      quickActions: [],
      resumeLesson: null,
    }) as DashboardData,
    tr,
  );
}

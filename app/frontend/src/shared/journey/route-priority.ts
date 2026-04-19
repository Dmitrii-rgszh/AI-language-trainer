import { routes } from "../constants/routes";
import { describeRouteDayShape } from "./route-day-shape";
import type { DashboardData, QuickAction } from "../types/app-data";
import { readRouteReentrySequenceState } from "./route-reentry-sequence";

export type RoutePriorityView = {
  mode:
    | "resume_route"
    | "route_rebuild"
    | "protected_return"
    | "skill_repair_cycle"
    | "targeted_stabilization"
    | "steady_extension"
    | "checkpoint"
    | "recovery"
    | "today_route"
    | "lesson";
  label: string;
  summary: string;
  primaryRoute: string;
  supportRoute?: string | null;
  reopenStageLabel?: string | null;
  expansionStageLabel?: string | null;
};

export type RouteProtectionView = {
  isSoftLockActive: boolean;
  protectedRoutes: string[];
  deferredRoutes: string[];
  deferredLabel: string;
  deferredReason: string;
};

export type ScreenRouteGovernanceView = {
  state: "open" | "protected_hold" | "priority_reentry" | "sequenced_hold";
  isDeferred: boolean;
  isMicroflowLocked: boolean;
  isPriorityReentry: boolean;
  badgeLabel: string;
  title: string;
  summary: string;
  primaryLabel: string;
  primaryRoute: string;
  secondaryLabel: string;
  secondaryRoute: string;
  dayShapeTitle?: string | null;
  dayShapeSummary?: string | null;
  dayShapeCompactnessLabel?: string | null;
  dayShapeSequenceLabel?: string | null;
  dayShapeExpansionStageLabel?: string | null;
  dayShapeExpansionWindowLabel?: string | null;
};

export function isSensitiveRoutePriorityMode(mode: RoutePriorityView["mode"]): boolean {
  return mode === "route_rebuild" || mode === "protected_return";
}

export function buildRoutePriorityView(
  dashboard: DashboardData | null,
  tr: (value: string) => string,
): RoutePriorityView {
  const plan = dashboard?.dailyLoopPlan ?? null;
  const recommendation = dashboard?.recommendation ?? null;
  const routeEntryMemory = dashboard?.journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const routeReentryProgress = dashboard?.journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const recoveryMemory = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const reopenSupportRoute =
    routeEntryMemory?.readyToReopenActiveNextRoute && routeEntryMemory.activeNextRoute
      ? routeEntryMemory.activeNextRoute
      : routeReentryProgress?.nextRoute ?? null;
  const reopenSupportLabel =
    reopenSupportRoute ? mapSupportRouteLabel(reopenSupportRoute, tr) ?? reopenSupportRoute : null;
  const reopenStageLabel =
    recoveryMemory?.reopenStage === "first_reopen"
      ? tr("First reopen")
      : recoveryMemory?.reopenStage === "settling_back_in"
        ? tr("Settling pass")
        : recoveryMemory?.reopenStage === "ready_to_expand"
          ? tr("Ready to widen")
          : null;
  const expansionStageLabel =
    recoveryMemory?.decisionWindowStage === "first_widening_pass"
      ? tr("First widening pass")
      : recoveryMemory?.decisionWindowStage === "stabilizing_widening"
        ? tr("Stabilizing widening")
        : recoveryMemory?.decisionWindowStage === "ready_for_extension"
          ? tr("Ready for extension")
          : null;

  if (plan?.lessonRunId && !plan.completedAt) {
    return {
      mode: "resume_route",
      label: tr("Resume today’s route"),
      summary: tr("The strongest next move is to return to the active route instead of opening a parallel module."),
      primaryRoute: routes.lessonRunner,
      supportRoute: reopenSupportRoute,
      reopenStageLabel,
      expansionStageLabel,
    };
  }

  if (plan && !plan.completedAt) {
    const focusLabel = recoveryMemory?.focusSkill ?? plan.focusArea;
    if (recoveryMemory?.phase === "support_reopen_arc" && reopenSupportRoute && reopenSupportLabel) {
      if (recoveryMemory.reopenStage === "first_reopen") {
        return {
          mode: "targeted_stabilization",
          label: tr(`Reopen ${reopenSupportLabel}`),
          summary: tr(`Today's route should reopen through ${reopenSupportLabel} first, before the wider mix starts moving again.`),
          primaryRoute: reopenSupportRoute,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      }

      if (recoveryMemory.reopenStage === "settling_back_in") {
        return {
          mode: "targeted_stabilization",
          label: tr(`Continue ${reopenSupportLabel}`),
          summary: tr(`The route is settling ${reopenSupportLabel} back into the connected flow, so this support pass should still come first.`),
          primaryRoute: reopenSupportRoute,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      }

      if (recoveryMemory.reopenStage === "ready_to_expand") {
        return {
          mode: "steady_extension",
          label:
            recoveryMemory.decisionWindowStage === "first_widening_pass"
              ? tr("Start widening pass")
              : recoveryMemory.decisionWindowStage === "stabilizing_widening"
                ? tr("Stabilize wider route")
                : recoveryMemory.decisionWindowStage === "ready_for_extension"
                  ? tr("Extend the route")
                  : tr("Return to wider route"),
          summary:
            recoveryMemory.decisionWindowStage === "first_widening_pass"
              ? tr(`The reopened ${reopenSupportLabel} is stable enough for a first widening pass, so the daily route should lead while keeping it quietly available.`)
              : recoveryMemory.decisionWindowStage === "stabilizing_widening"
                ? tr(`The first wider pass has landed, so the next route should stabilize that broader mix before extending further.`)
                : recoveryMemory.decisionWindowStage === "ready_for_extension"
                  ? tr(`The widening window has held, so the route can extend further while ${reopenSupportLabel} stays as support instead of a lead branch.`)
                  : tr(`The reopened ${reopenSupportLabel} is stable enough, so the main route can widen again while keeping it in rotation.`),
          primaryRoute: routes.dailyLoop,
          supportRoute:
            recoveryMemory.decisionWindowStage === "first_widening_pass"
              ? reopenSupportRoute
              : recoveryMemory.decisionWindowStage === "stabilizing_widening"
                ? reopenSupportRoute
                : reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      }
    }

    switch (recoveryMemory?.phase) {
      case "route_rebuild":
        return {
          mode: "route_rebuild",
          label: tr("Restart gently"),
          summary: tr(`The route is rebuilding, so the next click should reopen the habit softly around ${focusLabel}.`),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      case "protected_return":
        return {
          mode: "protected_return",
          label: tr("Continue protected return"),
          summary: tr(`The route is back in motion, but it should still stay protected around ${focusLabel} before it widens.`),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      case "skill_repair_cycle":
        return {
          mode: "skill_repair_cycle",
          label: tr("Start repair cycle"),
          summary: tr(`The next route should keep returning to ${focusLabel} on purpose across several sessions.`),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      case "targeted_stabilization":
        return {
          mode: "targeted_stabilization",
          label: tr("Stabilize the route"),
          summary: tr(`The next route should keep ${focusLabel} protected before it broadens again.`),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      case "steady_extension":
        return {
          mode: "steady_extension",
          label: tr("Keep the rhythm going"),
          summary: tr(`The route can extend forward now, while still protecting ${focusLabel}.`),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
      default:
        return {
          mode: "today_route",
          label: tr("Start today’s route"),
          summary: tr("The strongest next move is the connected route that has already been assembled for today."),
          primaryRoute: routes.dailyLoop,
          supportRoute: reopenSupportRoute,
          reopenStageLabel,
          expansionStageLabel,
        };
    }
  }

  if (recommendation?.lessonType === "recovery") {
    return {
      mode: "recovery",
      label: tr("Start recovery"),
      summary: tr("Right now the best next step is a narrower recovery route before the system broadens again."),
      primaryRoute: routes.activity,
      supportRoute: reopenSupportRoute,
      reopenStageLabel,
      expansionStageLabel,
    };
  }

  if (dashboard?.journeyState?.diagnosticReadiness === "checkpoint_now") {
    return {
      mode: "checkpoint",
      label: tr("Start checkpoint"),
      summary: tr("Right now the strongest next step is a checkpoint so the route can become more precise."),
      primaryRoute: routes.progress,
      supportRoute: reopenSupportRoute,
      reopenStageLabel,
      expansionStageLabel,
    };
  }

  return {
    mode: "lesson",
    label: tr("Start lesson"),
    summary: tr("Open the next lesson and let the route continue through the main guided flow."),
    primaryRoute: routes.lessonRunner,
    supportRoute: reopenSupportRoute,
    reopenStageLabel,
    expansionStageLabel,
  };
}

export function buildBiasedQuickActions(
  dashboard: DashboardData | null,
  baseActions: QuickAction[],
  tr: (value: string) => string,
): QuickAction[] {
  const priority = buildRoutePriorityView(dashboard, tr);
  const protection = buildRouteProtectionView(dashboard, tr);
  const plan = dashboard?.dailyLoopPlan ?? null;
  const journeyState = dashboard?.journeyState ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape = plan
    ? describeRouteDayShape(plan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr)
    : null;
  const routeHref = priority.primaryRoute;

  const primaryAction: QuickAction = {
    id: "route-priority-main",
    title: priority.label,
    description: dayShape
      ? `${priority.summary} ${tr("Day shape")}: ${dayShape.title}${dayShape.compactnessLabel ? ` · ${dayShape.compactnessLabel}` : ""}.`
      : priority.summary,
    route: routeHref,
    tone: "primary",
  };

  const supportRouteOrder: string[] = priority.supportRoute
    ? priority.expansionStageLabel === tr("Ready for extension")
      ? [routes.dailyLoop, routes.activity, routes.progress, priority.supportRoute]
      : priority.expansionStageLabel === tr("Stabilizing widening")
        ? [routes.dailyLoop, priority.supportRoute, routes.activity, routes.progress]
        : priority.reopenStageLabel === tr("Ready to widen") || priority.expansionStageLabel === tr("First widening pass")
          ? [routes.dailyLoop, priority.supportRoute, routes.activity, routes.progress]
          : [priority.supportRoute, routes.dailyLoop, routes.activity, routes.progress]
    : priority.mode === "checkpoint"
      ? [routes.progress, routes.dailyLoop, routes.activity]
      : priority.mode === "recovery"
        ? [routes.activity, routes.progress, routes.dailyLoop]
        : [routes.dailyLoop, routes.activity, routes.progress];

  const supportActions = baseActions
    .filter((action) => supportRouteOrder.includes(action.route))
    .sort((left, right) => supportRouteOrder.indexOf(left.route) - supportRouteOrder.indexOf(right.route))
    .map((action, index) => ({
      ...action,
      tone: "support" as const,
      description:
        index === 0 && dayShape
          ? `${action.description} ${tr("This keeps the route inside")} ${dayShape.title.toLowerCase()}.`
          : action.description,
    }));

  const remainingActions = baseActions
    .filter((action) => !supportRouteOrder.includes(action.route))
    .map((action) => ({
      ...action,
      tone: action.tone ?? "default" as const,
      disabled:
        protection.isSoftLockActive && protection.deferredRoutes.includes(action.route),
      disabledReason:
        protection.isSoftLockActive && protection.deferredRoutes.includes(action.route)
          ? dayShape
            ? `${protection.deferredReason} ${tr("Current day shape")}: ${dayShape.title}.`
            : protection.deferredReason
          : null,
    }));

  const routeFocus = journeyState?.strategySnapshot.routeRecoveryMemory?.focusSkill ?? journeyState?.currentFocusArea ?? null;
  const alignedRoute =
    routeFocus === "grammar"
      ? routes.grammar
      : routeFocus === "speaking"
        ? routes.speaking
        : routeFocus === "pronunciation"
          ? routes.pronunciation
          : routeFocus === "writing"
            ? routes.writing
            : routeFocus === "profession"
              ? routes.profession
          : routeFocus === "vocabulary"
                ? routes.vocabulary
                : routeFocus === "listening"
                  ? routes.listening
                : routeFocus === "reading"
                  ? routes.reading
                : null;
  const alignedAction = alignedRoute
    ? remainingActions.find((action) => action.route === alignedRoute)
    : null;
  const rest = remainingActions.filter((action) => action !== alignedAction);

  return [
    primaryAction,
    ...supportActions,
    ...(alignedAction && !alignedAction.disabled ? [{ ...alignedAction, tone: "support" as const }] : []),
    ...rest,
  ].slice(0, 5);
}

export function buildRouteProtectionView(
  dashboard: DashboardData | null,
  tr: (value: string) => string,
): RouteProtectionView {
  const priority = buildRoutePriorityView(dashboard, tr);
  const protectedRoutes =
    isSensitiveRoutePriorityMode(priority.mode)
      ? [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress, routes.lessonRunner]
      : [routes.dashboard, routes.dailyLoop, routes.activity, routes.progress];
  const allSideRoutes = [
    routes.vocabulary,
    routes.listening,
    routes.reading,
    routes.grammar,
    routes.speaking,
    routes.pronunciation,
    routes.writing,
    routes.profession,
    routes.mistakes,
    routes.liveAvatar,
    routes.settings,
  ];
  const isSoftLockActive = isSensitiveRoutePriorityMode(priority.mode);

  return {
    isSoftLockActive,
    protectedRoutes,
    deferredRoutes: isSoftLockActive ? allSideRoutes : [],
    deferredLabel: isSoftLockActive ? tr("Later in the route") : tr("Open route"),
    deferredReason: isSoftLockActive
      ? tr("The system is protecting the main route right now, so side modules should wait until today's return is complete.")
      : tr("This route is ready to open."),
  };
}

export function buildScreenRouteGovernanceView(
  dashboard: DashboardData | null,
  currentRoute: string,
  tr: (value: string) => string,
): ScreenRouteGovernanceView {
  const priority = buildRoutePriorityView(dashboard, tr);
  const protection = buildRouteProtectionView(dashboard, tr);
  const plan = dashboard?.dailyLoopPlan ?? null;
  const recoveryMemory = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = dashboard?.journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = dashboard?.journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape = plan
    ? describeRouteDayShape(plan, recoveryMemory, routeReentryProgress, routeEntryMemory, tr)
    : null;
  const sequenceState = readRouteReentrySequenceState(dashboard);
  const primaryRoute =
    plan && !plan.completedAt
      ? routes.dailyLoop
      : priority.mode === "checkpoint"
        ? routes.progress
        : priority.mode === "recovery"
          ? routes.activity
          : routes.dashboard;
  const isDeferred = protection.isSoftLockActive && protection.deferredRoutes.includes(currentRoute);
  const sharedDayShapeFields = {
    dayShapeTitle: dayShape?.title ?? null,
    dayShapeSummary: dayShape?.summary ?? null,
    dayShapeCompactnessLabel: dayShape?.compactnessLabel ?? null,
    dayShapeSequenceLabel: dayShape?.sequenceLabel ?? null,
    dayShapeExpansionStageLabel: dayShape?.expansionStageLabel ?? null,
    dayShapeExpansionWindowLabel: dayShape?.expansionWindowLabel ?? null,
  };

  if (isDeferred) {
    return {
      state: "protected_hold",
      isDeferred: true,
      isMicroflowLocked: true,
      isPriorityReentry: false,
      badgeLabel: tr("Later in the route"),
      title: tr("Protected return is active"),
      summary: dayShape
        ? tr(`This screen can still help, but today's ${dayShape.title} should stay protected instead of turning into a separate branch.`)
        : tr("This screen can still help, but right now it should support today's protected route instead of becoming a separate branch."),
      primaryLabel: priority.label,
      primaryRoute,
      secondaryLabel: tr("Open dashboard overview"),
      secondaryRoute: routes.dashboard,
      ...sharedDayShapeFields,
    };
  }

  if (sequenceState.isActive && sequenceState.nextRoute && currentRoute === sequenceState.nextRoute) {
    const reopenLabel = recoveryMemory?.supportPracticeTitle ?? dashboard?.journeyState?.currentFocusArea ?? tr("the active skill");
    return {
      state: "priority_reentry",
      isDeferred: false,
      isMicroflowLocked: false,
      isPriorityReentry: true,
      badgeLabel: tr("Reopened now"),
      title: tr("This skill is back in focus"),
      summary: dayShape
        ? tr(`The route is reopening in sequence, and ${reopenLabel} is the right support surface to use now inside today's ${dayShape.title}.`)
        : tr(`The route is reopening in sequence, and ${reopenLabel} is the right support surface to use now.`),
      primaryLabel: tr("Keep route in motion"),
      primaryRoute: routes.dailyLoop,
      secondaryLabel: tr("Open dashboard overview"),
      secondaryRoute: routes.dashboard,
      ...sharedDayShapeFields,
    };
  }

  if (sequenceState.isActive && sequenceState.nextRoute && protection.deferredRoutes.includes(currentRoute) && !sequenceState.completedRoutes.includes(currentRoute)) {
    return {
      state: "sequenced_hold",
      isDeferred: true,
      isMicroflowLocked: true,
      isPriorityReentry: false,
      badgeLabel: tr("Reopens later"),
      title: tr("Another support surface should reopen first"),
      summary: dayShape?.sequenceLabel
        ? tr(`The route is widening again, but ${dayShape.sequenceLabel} should reopen before this branch comes back into active use.`)
        : tr("The route is widening again, but another support surface should reopen before this branch comes back into active use."),
      primaryLabel: tr("Open focused re-entry"),
      primaryRoute: sequenceState.nextRoute,
      secondaryLabel: tr("Open daily loop"),
      secondaryRoute: routes.dailyLoop,
      ...sharedDayShapeFields,
    };
  }

  return {
    state: "open",
    isDeferred: false,
    isMicroflowLocked: false,
    isPriorityReentry: false,
    badgeLabel: tr("Route is open"),
    title: tr("Route is open"),
    summary: dayShape
      ? tr(`This screen is available as part of today's ${dayShape.title}.`)
      : tr("This screen is available as part of the current route."),
    primaryLabel: priority.label,
    primaryRoute,
    secondaryLabel: tr("Open daily loop"),
    secondaryRoute: routes.dailyLoop,
    ...sharedDayShapeFields,
  };
}

function mapSupportRouteLabel(route: string, tr: (value: string) => string): string | null {
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
    }[route] ?? null
  );
}

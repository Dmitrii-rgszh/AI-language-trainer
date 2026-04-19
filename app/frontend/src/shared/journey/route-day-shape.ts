import type { DailyLoopPlan, RouteEntryMemory, RouteRecoveryMemory, RouteReentryProgressMemory } from "../types/app-data";

export type RouteDayShapeDescriptor = {
  shapeKey: string;
  title: string;
  summary: string;
  compactnessLabel: string;
  sequenceLabel?: string | null;
  releaseLabel?: string | null;
  substageLabel?: string | null;
  expansionStageLabel?: string | null;
  expansionWindowLabel?: string | null;
};

function describeRouteEntryReset(
  routeEntryMemory: RouteEntryMemory | null | undefined,
  tr: (value: string) => string,
): { label: string; visits: number } | null {
  const activeNextRoute = routeEntryMemory?.activeNextRoute;
  const activeNextRouteVisits = routeEntryMemory?.activeNextRouteVisits ?? 0;
  if (!activeNextRoute || activeNextRouteVisits < 2) {
    return null;
  }

  return {
    label: mapRouteLabel(activeNextRoute, tr) ?? activeNextRoute,
    visits: activeNextRouteVisits,
  };
}

function describeRouteEntryRelease(
  routeEntryMemory: RouteEntryMemory | null | undefined,
  tr: (value: string) => string,
): { label: string; visits: number } | null {
  const activeNextRoute = routeEntryMemory?.activeNextRoute;
  if (!activeNextRoute || !routeEntryMemory?.readyToReopenActiveNextRoute) {
    return null;
  }

  return {
    label: mapRouteLabel(activeNextRoute, tr) ?? activeNextRoute,
    visits: routeEntryMemory.connectedResetVisits ?? 0,
  };
}

function mapRouteLabel(route: string | null | undefined, tr: (value: string) => string): string | null {
  if (!route) {
    return null;
  }

  return (
    {
      "/grammar": tr("grammar support"),
      "/vocabulary": tr("vocabulary support"),
      "/speaking": tr("speaking support"),
      "/pronunciation": tr("pronunciation support"),
      "/writing": tr("writing support"),
      "/profession": tr("professional support"),
    }[route] ?? route
  );
}

function buildCompactnessLabel(
  plan: DailyLoopPlan,
  tr: (value: string) => string,
): string {
  if (plan.estimatedMinutes <= 18 || plan.steps.length <= 6) {
    return tr("Compact day");
  }
  if (plan.estimatedMinutes >= 26 || plan.steps.length >= 8) {
    return tr("Extended day");
  }
  return tr("Standard day");
}

function describeExpansionStage(
  routeRecoveryMemory: RouteRecoveryMemory | null | undefined,
  tr: (value: string) => string,
): { label: string; windowLabel: string | null } | null {
  if (routeRecoveryMemory?.decisionBias !== "widening_window") {
    return null;
  }

  const remainingDays = routeRecoveryMemory.decisionWindowRemainingDays ?? routeRecoveryMemory.decisionWindowDays ?? null;
  const windowLabel =
    remainingDays && remainingDays > 0
      ? tr(`${remainingDays} route decisions left in the widening window`)
      : null;

  if (routeRecoveryMemory.decisionWindowStage === "first_widening_pass") {
    return {
      label: tr("First widening pass"),
      windowLabel,
    };
  }
  if (routeRecoveryMemory.decisionWindowStage === "stabilizing_widening") {
    return {
      label: tr("Stabilizing widening"),
      windowLabel,
    };
  }
  if (routeRecoveryMemory.decisionWindowStage === "ready_for_extension") {
    return {
      label: tr("Ready for extension"),
      windowLabel,
    };
  }

  return windowLabel
    ? {
        label: tr("Controlled widening window"),
        windowLabel,
      }
    : null;
}

export function describeRouteDayShape(
  plan: DailyLoopPlan,
  routeRecoveryMemory: RouteRecoveryMemory | null | undefined,
  routeReentryProgress: RouteReentryProgressMemory | null | undefined,
  routeEntryMemory: RouteEntryMemory | null | undefined,
  tr: (value: string) => string,
): RouteDayShapeDescriptor {
  const compactnessLabel = buildCompactnessLabel(plan, tr);
  const nextRouteLabel = mapRouteLabel(routeReentryProgress?.nextRoute, tr);
  const routeEntryReset = describeRouteEntryReset(routeEntryMemory, tr);
  const routeEntryRelease = describeRouteEntryRelease(routeEntryMemory, tr);

  const shapeKey = routeRecoveryMemory?.sessionShape ?? "default_route";
  const focusSkill = routeRecoveryMemory?.focusSkill ?? plan.focusArea;
  const horizonDays = routeRecoveryMemory?.horizonDays ?? null;
  const reopenStage = routeRecoveryMemory?.reopenStage ?? null;
  const expansionStage = describeExpansionStage(routeRecoveryMemory, tr);

  function describeReopenSubstage(): string | null {
    if (reopenStage === "first_reopen") {
      return tr("First reopen");
    }
    if (reopenStage === "settling_back_in") {
      return tr("Settling pass");
    }
    if (reopenStage === "ready_to_expand") {
      return tr("Ready to widen");
    }
    return null;
  }

  if (shapeKey === "gentle_restart") {
    return {
      shapeKey,
      title: tr("Gentle restart"),
      summary: nextRouteLabel
        ? tr(`This day stays short and finishable, then reopens through ${nextRouteLabel}.`)
        : tr(`This day stays short and finishable so ${focusSkill} can come back without overload.`),
      compactnessLabel,
      sequenceLabel: nextRouteLabel,
    };
  }

  if (shapeKey === "protected_mix") {
    return {
      shapeKey,
      title: routeEntryReset
        ? tr("Connected reset")
        : routeEntryRelease
          ? tr("Support reopen ready")
          : tr("Protected return"),
      summary: routeEntryReset
        ? tr(
            `The route stays connected for a calmer reset day before reopening ${routeEntryReset.label} again.`,
          )
        : routeEntryRelease
          ? tr(
              reopenStage === "ready_to_expand"
                ? expansionStage?.label === tr("First widening pass")
                  ? `${routeEntryRelease.label} has settled back into the connected route, so today should work as the first widening pass without dropping it.`
                  : expansionStage?.label === tr("Stabilizing widening")
                    ? `${routeEntryRelease.label} survived the first wider pass, so today should stabilize that broader mix once more before the route extends further.`
                    : expansionStage?.label === tr("Ready for extension")
                      ? `${routeEntryRelease.label} has already held across the widening window, so today can begin extending the route further while keeping it quietly available.`
                      : `${routeEntryRelease.label} has already settled back into the connected route, so today can start widening again without dropping it.`
                : reopenStage === "settling_back_in"
                  ? `${routeEntryRelease.label} is back inside the connected route, and today gives it one more settling pass before the route widens again.`
                  : `The calmer reset has done its job, so ${routeEntryRelease.label} can reopen inside today's connected route.`,
            )
        : nextRouteLabel
          ? tr(`The route reopens carefully, with ${nextRouteLabel} lifted earlier before the wider mix returns.`)
          : tr(`The route reopens carefully and keeps ${focusSkill} protected before it widens again.`),
      compactnessLabel,
      sequenceLabel: routeEntryReset?.label ?? routeEntryRelease?.label ?? nextRouteLabel,
      releaseLabel: routeEntryRelease?.label ?? null,
      substageLabel: describeReopenSubstage(),
      expansionStageLabel: expansionStage?.label ?? null,
      expansionWindowLabel: expansionStage?.windowLabel ?? null,
    };
  }

  if (shapeKey === "focused_support" || shapeKey === "repair_mix") {
    return {
      shapeKey,
      title: tr("Focused support"),
      summary: nextRouteLabel
        ? tr(`This day is shaped around the repair sequence, so ${nextRouteLabel} appears early instead of getting buried later.`)
        : tr(`This day keeps a tighter repair focus on ${focusSkill} across the next ${horizonDays ?? 2} routes.`),
      compactnessLabel,
      sequenceLabel: nextRouteLabel,
      releaseLabel: routeEntryRelease?.label ?? null,
      substageLabel: describeReopenSubstage(),
    };
  }

  if (shapeKey === "guided_balance") {
    return {
      shapeKey,
      title: tr("Guided balance"),
      summary: nextRouteLabel
        ? expansionStage?.label === tr("First widening pass")
          ? tr(`The route is using a first widening pass, so ${nextRouteLabel} stays available while the broader daily flow leads again.`)
          : expansionStage?.label === tr("Stabilizing widening")
            ? tr(`The route is stabilizing its broader widening mix, so ${nextRouteLabel} stays connected without reclaiming the whole session.`)
            : expansionStage?.label === tr("Ready for extension")
              ? tr(`The route has already stabilized the widening window, so ${nextRouteLabel} can stay quiet while the broader flow begins extending further.`)
              : tr(`The route keeps balance, but still lifts ${nextRouteLabel} early enough to stabilize the next step.`)
        : expansionStage?.label === tr("First widening pass")
          ? tr(`The route is using a first widening pass: the broader flow leads again while ${focusSkill} stays available inside it.`)
          : expansionStage?.label === tr("Stabilizing widening")
            ? tr(`The route is stabilizing its wider mix, so ${focusSkill} stays connected without dominating the whole day.`)
            : expansionStage?.label === tr("Ready for extension")
              ? tr(`The controlled widening window has held, so the route can begin extending forward again while ${focusSkill} stays as quiet support.`)
              : tr(`The route stays balanced while it stabilizes ${focusSkill} before widening again.`),
      compactnessLabel,
      sequenceLabel: nextRouteLabel,
      releaseLabel: routeEntryRelease?.label ?? null,
      substageLabel: describeReopenSubstage(),
      expansionStageLabel: expansionStage?.label ?? null,
      expansionWindowLabel: expansionStage?.windowLabel ?? null,
    };
  }

  if (shapeKey === "forward_mix") {
    return {
      shapeKey,
      title: tr("Forward extension"),
      summary: nextRouteLabel
        ? tr(`The route can extend forward, while still reopening through ${nextRouteLabel} in sequence.`)
        : tr(`The route can stretch a bit wider now because the daily rhythm is holding.`),
      compactnessLabel,
      sequenceLabel: nextRouteLabel,
      releaseLabel: routeEntryRelease?.label ?? null,
      substageLabel: describeReopenSubstage(),
      expansionStageLabel: expansionStage?.label ?? null,
      expansionWindowLabel: expansionStage?.windowLabel ?? null,
    };
  }

  return {
    shapeKey,
    title: tr("Guided route"),
    summary: nextRouteLabel
      ? tr(`The route stays connected and still reopens through ${nextRouteLabel} when needed.`)
      : tr("The route stays connected instead of splitting into disconnected drills."),
    compactnessLabel,
    sequenceLabel: nextRouteLabel,
    releaseLabel: routeEntryRelease?.label ?? null,
    substageLabel: describeReopenSubstage(),
    expansionStageLabel: expansionStage?.label ?? null,
    expansionWindowLabel: expansionStage?.windowLabel ?? null,
  };
}

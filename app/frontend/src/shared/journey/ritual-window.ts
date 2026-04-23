import type { RitualSignalMemory } from "../types/app-data";

export type RitualWindowDescriptor = {
  stageKey: string;
  title: string;
  summary: string;
  hint?: string | null;
  windowLabel?: string | null;
};

export function describeRitualWindow(
  ritualSignalMemory: RitualSignalMemory | null | undefined,
  tr: (value: string) => string,
): RitualWindowDescriptor | null {
  if (!ritualSignalMemory) {
    return null;
  }

  const routeWindowStage = ritualSignalMemory.routeWindowStage ?? null;
  const label = ritualSignalMemory.activeLabel ?? tr("the ritual signal");
  const remainingDays =
    ritualSignalMemory.windowRemainingDays ?? ritualSignalMemory.windowDays ?? null;
  const windowLabel =
    remainingDays && remainingDays > 0
      ? tr(`${remainingDays} route decisions left in the ritual window`)
      : null;

  if (routeWindowStage === "protect_ritual") {
    return {
      stageKey: routeWindowStage,
      title: tr("Protect ritual"),
      summary:
        ritualSignalMemory.summary ??
        tr(`Keep ${label} inside a protected ritual pass before the broader route widens.`),
      hint: ritualSignalMemory.actionHint ?? null,
      windowLabel,
    };
  }

  if (routeWindowStage === "reuse_in_response") {
    return {
      stageKey: routeWindowStage,
      title: tr("Reuse in response"),
      summary:
        ritualSignalMemory.summary ??
        tr(`Bring ${label} directly into one more response so the ritual signal starts living inside the route.`),
      hint: ritualSignalMemory.actionHint ?? null,
      windowLabel,
    };
  }

  if (routeWindowStage === "carry_inside_route") {
    return {
      stageKey: routeWindowStage,
      title: tr("Carry inside route"),
      summary:
        ritualSignalMemory.summary ??
        tr(`Let the broader route lead again while ${label} stays available as a quiet carry-over.`),
      hint: ritualSignalMemory.actionHint ?? null,
      windowLabel,
    };
  }

  return ritualSignalMemory.windowStage
    ? {
        stageKey: ritualSignalMemory.windowStage,
        title: tr("Ritual window"),
        summary: ritualSignalMemory.summary ?? tr("The route is carrying a ritual signal across connected days."),
        hint: ritualSignalMemory.actionHint ?? null,
        windowLabel,
      }
    : null;
}

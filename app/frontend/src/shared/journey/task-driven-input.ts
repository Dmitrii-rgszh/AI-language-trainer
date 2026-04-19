import { routes } from "../constants/routes";
import type { DailyLoopPlan, LearnerJourneyState } from "../types/app-data";

export type TaskDrivenInputSurface = {
  route: string;
  label: string;
  title: string;
  summary: string;
  bridge: string;
};

function normalizeToken(value: string | null | undefined) {
  return (value ?? "").trim().toLowerCase();
}

export function resolveTaskDrivenInputSurface(
  dailyLoopPlan: DailyLoopPlan | null,
  journeyState: LearnerJourneyState | null,
  tr: (value: string) => string,
): TaskDrivenInputSurface | null {
  if (!dailyLoopPlan || dailyLoopPlan.completedAt) {
    return null;
  }

  if (dailyLoopPlan.taskDrivenInput) {
    return {
      route: dailyLoopPlan.taskDrivenInput.inputRoute,
      label: dailyLoopPlan.taskDrivenInput.inputLabel,
      title: dailyLoopPlan.taskDrivenInput.title,
      summary: dailyLoopPlan.taskDrivenInput.summary,
      bridge: dailyLoopPlan.taskDrivenInput.bridge,
    };
  }

  const inputStep =
    dailyLoopPlan.steps.find((step) => {
      const skill = normalizeToken(step.skill);
      const title = normalizeToken(step.title);
      const description = normalizeToken(step.description);
      return (
        skill === "reading" ||
        skill === "listening" ||
        title.includes("reading") ||
        title.includes("listening") ||
        description.includes("reading") ||
        description.includes("listening")
      );
    }) ?? null;

  const focusArea = journeyState?.currentFocusArea ?? dailyLoopPlan.focusArea;
  if (!inputStep) {
    return null;
  }

  const normalizedSkill = normalizeToken(inputStep.skill);
  if (normalizedSkill === "reading") {
    return {
      route: routes.reading,
      label: tr("reading support"),
      title: tr("Open reading input first"),
      summary: tr(`Today's route should open through a calmer reading pass before it moves into the response around ${focusArea}.`),
      bridge: tr("Start with the reading cue, then return to the guided route while the text signal is still fresh."),
    };
  }

  if (normalizedSkill === "listening") {
    return {
      route: routes.listening,
      label: tr("listening support"),
      title: tr("Open listening input first"),
      summary: tr(`Today's route should open through an audio-first pass before it moves into the response around ${focusArea}.`),
      bridge: tr("Start with the listening cue, then return to the guided route while the audio signal is still fresh."),
    };
  }

  return null;
}

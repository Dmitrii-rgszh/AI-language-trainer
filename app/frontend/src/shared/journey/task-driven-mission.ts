import { routes } from "../constants/routes";
import type { DashboardData } from "../types/app-data";

export type TaskDrivenMission = {
  inputRoute: string;
  inputLabel: string;
  responseRoute: string;
  responseLabel: string;
  title: string;
  summary: string;
  bridge: string;
  closure: string;
};

export function resolveTaskDrivenMission(
  dashboard: DashboardData | null,
  inputRoute: string,
  tr: (value: string) => string,
): TaskDrivenMission | null {
  if (!dashboard?.dailyLoopPlan) {
    return null;
  }

  if (dashboard.dailyLoopPlan.taskDrivenInput && dashboard.dailyLoopPlan.taskDrivenInput.inputRoute === inputRoute) {
    return {
      inputRoute: dashboard.dailyLoopPlan.taskDrivenInput.inputRoute,
      inputLabel: dashboard.dailyLoopPlan.taskDrivenInput.inputLabel,
      responseRoute: dashboard.dailyLoopPlan.taskDrivenInput.responseRoute,
      responseLabel: dashboard.dailyLoopPlan.taskDrivenInput.responseLabel,
      title: dashboard.dailyLoopPlan.taskDrivenInput.title,
      summary: dashboard.dailyLoopPlan.taskDrivenInput.summary,
      bridge: dashboard.dailyLoopPlan.taskDrivenInput.bridge,
      closure: dashboard.dailyLoopPlan.taskDrivenInput.closure,
    };
  }

  const preferredMode = dashboard.dailyLoopPlan.preferredMode;
  const focusArea = dashboard.journeyState?.currentFocusArea ?? dashboard.dailyLoopPlan.focusArea;
  const headline = dashboard.dailyLoopPlan.headline;
  const responseRoute =
    inputRoute === routes.reading
      ? preferredMode === "text_first"
        ? routes.writing
        : routes.lessonRunner
      : inputRoute === routes.listening
        ? preferredMode === "voice_first"
          ? routes.speaking
          : routes.lessonRunner
        : routes.lessonRunner;
  const responseLabel =
    responseRoute === routes.writing
      ? tr("writing response")
      : responseRoute === routes.speaking
        ? tr("spoken response")
        : tr("guided route");
  const inputLabel =
    inputRoute === routes.reading
      ? tr("reading input")
      : inputRoute === routes.listening
        ? tr("listening input")
        : tr("route input");

  return {
    inputRoute,
    inputLabel,
    responseRoute,
    responseLabel,
    title:
      inputRoute === routes.reading
        ? tr("Text signal mission")
        : inputRoute === routes.listening
          ? tr("Audio signal mission")
          : tr("Input mission"),
    summary:
      inputRoute === routes.reading
        ? tr(`Take one useful text signal from ${headline}, convert it into a clearer ${responseLabel}, and return it to the route around ${focusArea}.`)
        : tr(`Take one useful audio signal from ${headline}, convert it into a clearer ${responseLabel}, and return it to the route around ${focusArea}.`),
    bridge:
      responseRoute === routes.lessonRunner
        ? tr(`After the input pass, go straight back into the guided route while the signal is still fresh.`)
        : tr(`After the input pass, move the signal into ${responseLabel} before returning to the wider route.`),
    closure: tr(`The mission closes only after the ${responseLabel} feeds the next connected route step.`),
  };
}

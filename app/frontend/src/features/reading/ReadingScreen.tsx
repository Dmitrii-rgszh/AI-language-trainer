import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { resolveRouteFollowUpTransition } from "../../shared/journey/route-follow-up-navigation";
import { buildScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import { resolveTaskDrivenMission } from "../../shared/journey/task-driven-mission";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { RouteMicroflowGuard } from "../../widgets/journey/RouteMicroflowGuard";
import { RouteGovernanceNotice } from "../../widgets/journey/RouteGovernanceNotice";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

function buildReadingPass(dashboard: ReturnType<typeof useAppStore.getState>["dashboard"], tr: (value: string) => string) {
  const profile = dashboard?.profile ?? null;
  const plan = dashboard?.dailyLoopPlan ?? null;
  const blueprint = dashboard?.journeyState?.strategySnapshot.learningBlueprint ?? null;
  const recovery = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const goal = profile?.onboardingAnswers.primaryGoal
    ? tr(profile.onboardingAnswers.primaryGoal)
    : tr("steady spoken confidence");
  const professionTrack = profile?.professionTrack ? tr(profile.professionTrack) : tr("real-world communication");
  const focusArea = plan?.focusArea ? tr(plan.focusArea) : dashboard?.journeyState?.currentFocusArea ? tr(dashboard.journeyState.currentFocusArea) : tr("reading");
  const routeMode = blueprint?.currentPhaseLabel ?? tr("connected route");
  const routeHeadline = plan?.headline ? tr(plan.headline) : blueprint?.headline ? tr(blueprint.headline) : tr("Today’s route");
  const supportTitle = recovery?.supportPracticeTitle ?? tr("reading support");
  const passageTitle = tr("Reading brief for today’s route");
  const passage = tr(
    `Today's route is not asking you to read passively. It is asking you to extract one useful idea from a short text, connect it to ${goal}, and then carry it into ${professionTrack}. The route is currently protecting ${focusArea}, so this reading pass should stay practical: find the signal, keep the wording simple, and move the insight into your next response instead of treating reading like a separate subject.`,
  );
  const extractionPrompts = [
    tr(`What is the one sentence in this brief that matters most for ${goal}?`),
    tr(`Which phrase from this text would be useful in ${professionTrack}?`),
    tr(`How should this reading pass change your next ${supportTitle} move inside the route?`),
  ];
  const responseBridge = tr(
    `After this reading pass, do not stop at understanding. Use one extracted phrase or idea in the next writing, speaking, or guided route step so the reading signal actually enters the learning loop.`,
  );

  return {
    passageTitle,
    passage,
    extractionPrompts,
    responseBridge,
    routeHeadline,
    routeMode,
  };
}

export function ReadingScreen() {
  const { locale, tr } = useLocale();
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const navigate = useNavigate();
  const routeGovernance = buildScreenRouteGovernanceView(dashboard ?? null, routes.reading, tr);
  const readingPass = buildReadingPass(dashboard ?? null, tr);
  const taskMission = resolveTaskDrivenMission(dashboard ?? null, routes.reading, tr);
  const focusPillars = dashboard?.journeyState?.strategySnapshot.learningBlueprint?.focusPillars ?? [];
  const activePlanSteps = dashboard?.dailyLoopPlan?.steps ?? [];
  const replayCta = locale === "ru" ? "Послушать ещё раз" : "Hear it again";
  const coachMessage =
    locale === "ru"
      ? `Сейчас reading нужен не ради длинного текста, а ради одного полезного сигнала для маршрута. Возьми короткий смысловой фрагмент, вытащи рабочую формулировку и сразу перенеси её в следующий ответ.`
      : "Reading is here for one useful route signal, not for a long passive text. Pull out one working phrase or idea and carry it straight into the next response.";
  const coachSpokenMessage =
    locale === "ru"
      ? "Этот reading pass нужен, чтобы быстро снять смысл, а потом вернуть его в живой маршрут через следующий ответ."
      : "This reading pass is here to capture meaning quickly and then feed it back into the live route through the next response.";
  const coachSupportingText =
    routeGovernance.isPriorityReentry
      ? routeGovernance.summary
      : routeGovernance.isDeferred
        ? tr("Reading still matters here, but during a protected return it should reinforce today’s route instead of becoming a separate study branch.")
        : locale === "ru"
          ? `Сейчас reading должен работать как связующее звено: не отдельная библиотека текстов, а короткий умный input перед writing, speaking или следующим guided step.`
          : "Reading should work here as connective input, not as a separate library of texts. It should feed the next writing, speaking, or guided step.";

  async function handleCompleteSupportStep() {
    const updatedState = await apiClient.completeRouteReentrySupportStep({ route: routes.reading });
    await bootstrap();
    const transition = resolveRouteFollowUpTransition(updatedState, routes.reading, tr);
    if (transition) {
      navigate(transition.route, {
        state: {
          routeEntryReason: transition.reason,
          routeEntrySource: "support_step_follow_up",
          routeEntryFollowUpLabel: transition.nextLabel ?? null,
          routeEntryStageLabel: transition.stageLabel ?? null,
        },
      });
    }
  }

  function openMissionResponse() {
    if (!taskMission) {
      navigate(routes.lessonRunner);
      return;
    }

    void (async () => {
      const updatedState = await apiClient.completeTaskDrivenStep({
        inputRoute: routes.reading,
        responseRoute: taskMission.responseRoute,
      });
      await bootstrap();
      navigate(taskMission.responseRoute, {
        state: {
          routeEntryReason:
            locale === "ru"
              ? `Reading-проход уже снял полезный сигнал. Теперь переведи его в ${taskMission.responseLabel}, чтобы маршрут не остановился на понимании текста.`
              : `The reading pass has already captured a useful signal. Now move it into ${taskMission.responseLabel} so the route does not stop at understanding the text.`,
          routeEntrySource: "task_driven_handoff",
          routeEntryFollowUpLabel: updatedState.strategySnapshot.routeFollowUpMemory?.followUpLabel ?? tr("daily route"),
          routeEntryStageLabel: updatedState.strategySnapshot.routeFollowUpMemory?.stageLabel ?? taskMission.title,
        },
      });
    })();
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Reading Route")}
        title={tr("Reading Support")}
        description={tr("Short guided reading passes that feed the same route into writing, speaking, and the daily ritual instead of living as a separate skill silo.")}
      />

      <RouteGovernanceNotice governance={routeGovernance} tr={tr} />

      <LivingDepthSection id={livingDepthSectionIds.readingCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`reading:${dashboard?.dailyLoopPlan?.id ?? "no-plan"}:${dashboard?.journeyState?.updatedAt ?? "stable"}`}
          title={locale === "ru" ? "Liza Reading Layer" : "Liza Reading Layer"}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={locale}
          replayCta={replayCta}
          primaryAction={
            routeGovernance.isPriorityReentry ? (
              <Button type="button" onClick={() => void handleCompleteSupportStep()} className="proof-lesson-primary-button">
                {locale === "ru" ? "Завершить reading support step" : "Finish reading support step"}
              </Button>
            ) : (
              <Link to={routeGovernance.isDeferred ? routeGovernance.primaryRoute : routes.writing} className="proof-lesson-primary-button">
                {routeGovernance.isDeferred
                  ? routeGovernance.primaryLabel
                  : locale === "ru"
                    ? "Перенести insight в writing"
                    : "Move the insight into writing"}
              </Link>
            )
          }
          secondaryAction={
            <Link
              to={
                routeGovernance.isPriorityReentry
                  ? routeGovernance.primaryRoute
                  : routeGovernance.isDeferred
                    ? routeGovernance.secondaryRoute
                    : routes.lessonRunner
              }
              className="proof-lesson-secondary-action"
            >
              {routeGovernance.isPriorityReentry
                ? routeGovernance.primaryLabel
                : routeGovernance.isDeferred
                  ? routeGovernance.secondaryLabel
                  : locale === "ru"
                    ? "Вернуться в guided route"
                    : "Return to guided route"}
            </Link>
          }
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
        <Card className="space-y-4">
          {routeGovernance.isDeferred ? (
            <RouteMicroflowGuard
              tr={tr}
              label={routeGovernance.badgeLabel}
              dayShapeTitle={routeGovernance.dayShapeTitle}
              dayShapeCompactnessLabel={routeGovernance.dayShapeCompactnessLabel}
              dayShapeSummary={routeGovernance.dayShapeSummary}
              dayShapeExpansionStageLabel={routeGovernance.dayShapeExpansionStageLabel}
              dayShapeExpansionWindowLabel={routeGovernance.dayShapeExpansionWindowLabel}
              message={
                routeGovernance.state === "sequenced_hold"
                  ? tr("Reading support will reopen later in the re-entry sequence, after the currently focused support surface has done its job first.")
                  : tr("Reading is still visible for context, but active extraction work should wait until the protected return route has landed.")
              }
            />
          ) : null}

          <div>
            <div className="text-lg font-semibold text-ink">{readingPass.passageTitle}</div>
            <div className="mt-2 text-sm text-slate-500">
              {readingPass.routeHeadline} · {readingPass.routeMode}
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 p-4 text-sm leading-7 text-slate-700">{readingPass.passage}</div>

          <div className="rounded-2xl bg-sand/80 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Reading extraction prompts")}</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {readingPass.extractionPrompts.map((prompt) => (
                <div key={prompt}>• {prompt}</div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-mint/30 p-4 text-sm leading-6 text-slate-700">{readingPass.responseBridge}</div>
          {taskMission ? (
            <div className="rounded-2xl border border-accent/15 bg-accent/8 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Task mission")}</div>
              <div className="mt-2 text-lg font-semibold text-ink">{taskMission.title}</div>
              <div className="mt-3 text-sm leading-6 text-slate-700">{taskMission.summary}</div>
              <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">{tr("Bridge")}:</span> {taskMission.bridge}
              </div>
              <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">{tr("Closure")}:</span> {taskMission.closure}
              </div>
              <div className="mt-3 flex flex-wrap gap-3">
                <Button type="button" onClick={openMissionResponse} className="proof-lesson-primary-button">
                  {locale === "ru" ? `Перейти в ${taskMission.responseLabel}` : `Move into ${taskMission.responseLabel}`}
                </Button>
                <Link to={routes.lessonRunner} className="proof-lesson-secondary-action">
                  {locale === "ru" ? "Вернуться в guided route" : "Return to guided route"}
                </Link>
              </div>
            </div>
          ) : null}
        </Card>

        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Blueprint links")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
              {tr("This reading surface now acts as a real bridge between blueprint strategy and the next expressive step, instead of staying hidden inside the lesson engine.")}
            </div>
            {focusPillars.length > 0 ? (
              <div className="space-y-3">
                {focusPillars.slice(0, 3).map((pillar) => (
                  <div key={pillar.id} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                    <div className="font-semibold text-ink">{tr(pillar.title)}</div>
                    <div className="mt-2">{tr(pillar.reason)}</div>
                  </div>
                ))}
              </div>
            ) : null}
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Next connected moves")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Reading should not become the destination. The route should move from input to response, then back into the wider daily ritual.")}
            </div>
            {activePlanSteps.length > 0 ? (
              <div className="space-y-3">
                {activePlanSteps.slice(0, 3).map((step) => (
                  <div key={step.id} className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                    <div className="font-semibold text-ink">{tr(step.title)}</div>
                    <div className="mt-2">{tr(step.description)}</div>
                  </div>
                ))}
              </div>
            ) : null}
            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={openMissionResponse} className="proof-lesson-primary-button">
                {locale === "ru" ? `Открыть ${taskMission?.responseLabel ?? "response"}` : `Open ${taskMission?.responseLabel ?? "response"}`}
              </Button>
              <Link to={routes.lessonRunner} className="proof-lesson-secondary-action">
                {locale === "ru" ? "Вернуться в lesson flow" : "Return to lesson flow"}
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

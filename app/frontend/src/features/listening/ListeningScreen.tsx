import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { resolveRouteFollowUpTransition } from "../../shared/journey/route-follow-up-navigation";
import { buildScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import { resolveTaskDrivenMission } from "../../shared/journey/task-driven-mission";
import type { ListeningAttempt, ListeningTrend } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { RouteMicroflowGuard } from "../../widgets/journey/RouteMicroflowGuard";
import { RouteGovernanceNotice } from "../../widgets/journey/RouteGovernanceNotice";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

function buildListeningTask(
  dashboard: ReturnType<typeof useAppStore.getState>["dashboard"],
  listeningTrend: ListeningTrend | null,
  tr: (value: string) => string,
) {
  const profile = dashboard?.profile ?? null;
  const plan = dashboard?.dailyLoopPlan ?? null;
  const routeRecovery = dashboard?.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const listeningFocus = dashboard?.studyLoop?.listeningFocus ? tr(dashboard.studyLoop.listeningFocus) : tr("audio comprehension");
  const goal = profile?.onboardingAnswers.primaryGoal ? tr(profile.onboardingAnswers.primaryGoal) : tr("everyday communication");
  const professionTrack = profile?.professionTrack ? tr(profile.professionTrack) : tr("real communication");
  const transcriptRate = listeningTrend?.transcriptSupportRate ?? null;
  const weakestPrompt = listeningTrend?.weakestPrompts[0]?.label ? tr(listeningTrend.weakestPrompts[0].label) : null;

  return {
    title: tr("Guided listening pass for today"),
    summary:
      transcriptRate !== null
        ? tr(`Today's listening route is trying to reduce transcript dependence while keeping the signal useful for ${goal}.`)
        : tr(`Today's listening route is here to capture one clearer audio signal and feed it back into ${goal}.`),
    passage: tr(
      `Imagine you hear a short working update during ${professionTrack}: one speaker gives a simple status, one blocker, and one next step. Your job is not to catch every word. Your job is to identify the operational signal that matters for today's route and carry it into the next response.`,
    ),
    prompts: [
      weakestPrompt
        ? tr(`Listen carefully for the weak prompt area around ${weakestPrompt} and notice whether you can now catch it without leaning on the transcript.`)
        : tr(`Identify the one sentence that matters most for today's route without trying to transcribe everything.`),
      tr(`Pull out one phrase that would help you respond more clearly in ${professionTrack}.`),
      tr(`Decide what today's route should do next after this listening pass: respond, clarify, or stabilize the signal.`),
    ],
    supportHint:
      transcriptRate !== null
        ? tr(`Transcript support has been used in ${transcriptRate}% of recent listening attempts, so today's pass should aim for cleaner first-pass comprehension.`)
        : tr("Today's pass should stay short and useful: one audio signal, one extracted idea, one connected next move."),
    bridge:
      routeRecovery?.phase === "support_reopen_arc"
        ? tr("This listening pass should help the reopened route settle back into the main path instead of spinning into a separate audio drill.")
        : tr("After this listening pass, move straight into the next response so the audio signal becomes part of the same daily route."),
    listeningFocus,
    routeHeadline: plan?.headline ? tr(plan.headline) : tr("Today’s route"),
  };
}

export function ListeningScreen() {
  const { locale, tr } = useLocale();
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const navigate = useNavigate();
  const [attempts, setAttempts] = useState<ListeningAttempt[]>([]);
  const [trend, setTrend] = useState<ListeningTrend | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const routeGovernance = buildScreenRouteGovernanceView(dashboard ?? null, routes.listening, tr);
  const taskMission = resolveTaskDrivenMission(dashboard ?? null, routes.listening, tr);

  useEffect(() => {
    let isMounted = true;

    async function loadListening() {
      setIsLoading(true);
      try {
        const [nextAttempts, nextTrend] = await Promise.all([
          apiClient.getListeningHistory(),
          apiClient.getListeningTrends(),
        ]);
        if (!isMounted) {
          return;
        }
        setAttempts(nextAttempts);
        setTrend(nextTrend);
        setLoadingError(null);
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setLoadingError(error instanceof Error ? error.message : tr("Failed to load listening history"));
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadListening();
    return () => {
      isMounted = false;
    };
  }, [tr]);

  const listeningTask = useMemo(() => buildListeningTask(dashboard ?? null, trend, tr), [dashboard, trend, tr]);
  const replayCta = locale === "ru" ? "Послушать ещё раз" : "Hear it again";
  const coachMessage =
    locale === "ru"
      ? `Listening здесь должен работать не как отдельный тренажёр на угадывание слов, а как короткий route-input: уловить смысл, удержать слабый сигнал и сразу превратить его в следующий ответ.`
      : "Listening here should not feel like a separate guessing drill. It should act as short route input: catch the meaning, stabilize the weak signal, and turn it into the next response.";
  const coachSpokenMessage =
    locale === "ru"
      ? "Сейчас важно не услышать всё идеально, а вытащить один полезный сигнал и вернуть его в живой маршрут."
      : "The goal is not perfect hearing. The goal is to extract one useful signal and carry it back into the live route.";
  const coachSupportingText =
    routeGovernance.isPriorityReentry
      ? routeGovernance.summary
      : routeGovernance.isDeferred
        ? tr("Listening still helps today, but it should reinforce the protected return instead of becoming a separate audio branch.")
        : trend
          ? tr(`Listening now has real attempt memory: average score ${trend.averageScore}, transcript support ${trend.transcriptSupportRate}%, and recurring prompt clusters that can shape the next route.`)
          : tr("Listening now has its own route surface, so audio support can feed the main learning path instead of hiding only inside lesson blocks.");

  async function handleCompleteSupportStep() {
    const updatedState = await apiClient.completeRouteReentrySupportStep({ route: routes.listening });
    await bootstrap();
    const transition = resolveRouteFollowUpTransition(updatedState, routes.listening, tr);
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
        inputRoute: routes.listening,
        responseRoute: taskMission.responseRoute,
      });
      await bootstrap();
      navigate(taskMission.responseRoute, {
        state: {
          routeEntryReason:
            locale === "ru"
              ? `Listening-проход уже снял полезный аудио-сигнал. Теперь переведи его в ${taskMission.responseLabel}, чтобы маршрут не остановился на распознавании.`
              : `The listening pass has already captured a useful audio signal. Now move it into ${taskMission.responseLabel} so the route does not stop at recognition alone.`,
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
        eyebrow={tr("Listening Route")}
        title={tr("Listening Support")}
        description={tr("A short audio-first support surface that uses real listening history and trend memory to feed the next connected route step.")}
      />

      <RouteGovernanceNotice governance={routeGovernance} tr={tr} />

      <LivingDepthSection id={livingDepthSectionIds.listeningCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`listening:${dashboard?.dailyLoopPlan?.id ?? "no-plan"}:${trend?.averageScore ?? "no-trend"}:${attempts.length}`}
          title={locale === "ru" ? "Liza Listening Layer" : "Liza Listening Layer"}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={locale}
          replayCta={replayCta}
          primaryAction={
            routeGovernance.isPriorityReentry ? (
              <Button type="button" onClick={() => void handleCompleteSupportStep()} className="proof-lesson-primary-button">
                {locale === "ru" ? "Завершить listening support step" : "Finish listening support step"}
              </Button>
            ) : (
              <Link to={routeGovernance.isDeferred ? routeGovernance.primaryRoute : routes.speaking} className="proof-lesson-primary-button">
                {routeGovernance.isDeferred
                  ? routeGovernance.primaryLabel
                  : locale === "ru"
                    ? "Перенести сигнал в speaking"
                    : "Move the signal into speaking"}
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

      {loadingError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{loadingError}</div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[1.06fr_0.94fr]">
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
                  ? tr("Listening support will reopen later in the re-entry sequence, after the currently focused support surface has landed first.")
                  : tr("Listening remains visible for context, but active audio-first work should wait until the protected return route is stable.")
              }
            />
          ) : null}

          <div>
            <div className="text-lg font-semibold text-ink">{listeningTask.title}</div>
            <div className="mt-2 text-sm text-slate-500">
              {listeningTask.routeHeadline} · {listeningTask.listeningFocus}
            </div>
          </div>

          <div className="rounded-2xl bg-white/80 p-4 text-sm leading-7 text-slate-700">{listeningTask.summary}</div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm leading-7 text-slate-700">{listeningTask.passage}</div>

          <div className="rounded-2xl bg-white/76 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Audio-first prompts")}</div>
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              {listeningTask.prompts.map((prompt) => (
                <div key={prompt}>• {prompt}</div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-mint/30 p-4 text-sm leading-6 text-slate-700">{listeningTask.supportHint}</div>
          <div className="rounded-2xl bg-white/80 p-4 text-sm leading-6 text-slate-700">{listeningTask.bridge}</div>
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
            <div className="text-lg font-semibold text-ink">{tr("Listening trend memory")}</div>
            {isLoading ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Loading listening signals...")}</div>
            ) : trend ? (
              <>
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Average score")}: <span className="font-semibold text-ink">{trend.averageScore}</span>
                </div>
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                  {tr("Transcript support rate")}: <span className="font-semibold text-ink">{trend.transcriptSupportRate}%</span>
                </div>
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                  {trend.weakestPrompts.length > 0
                    ? `${tr("Recurring weak prompts")}: ${trend.weakestPrompts.map((item) => `${item.label} (${item.occurrences}x)`).join(", ")}.`
                    : tr("No recurring weak listening prompt has emerged yet.")}
                </div>
              </>
            ) : (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Listening trend will appear after more audio-first attempts.")}</div>
            )}
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Recent listening attempts")}</div>
            {isLoading ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Loading recent attempts...")}</div>
            ) : attempts.length === 0 ? (
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                {tr("Listening attempts will appear here after completing audio-first lesson blocks.")}
              </div>
            ) : (
              attempts.slice(0, 4).map((attempt) => (
                <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-ink">{tr(attempt.lessonTitle)}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                        {attempt.promptLabel ? tr(attempt.promptLabel) : tr(attempt.blockTitle)}
                      </div>
                    </div>
                    <div className="text-sm text-slate-600">
                      {tr("score")} {attempt.score}
                    </div>
                  </div>
                  <div className="mt-3 text-sm text-slate-600">{attempt.answerSummary}</div>
                  <div className="mt-2 text-xs text-slate-500">
                    {attempt.usedTranscriptSupport ? tr("Transcript support used") : tr("Audio-first answer")}
                  </div>
                </div>
              ))
            )}

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

import { Link, useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { buildRouteFollowUpHintFromState } from "../../shared/journey/route-entry-orchestration";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { describeRitualWindow } from "../../shared/journey/ritual-window";
import { resolveTaskDrivenInputSurface } from "../../shared/journey/task-driven-input";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LizaGuidanceGrid } from "../../widgets/liza/LizaGuidanceGrid";
import { JourneySessionSummaryPanel } from "../../widgets/journey/JourneySessionSummaryPanel";
import { DailyRitualPanel } from "../../widgets/journey/DailyRitualPanel";

export function DailyLoopScreen() {
  const { tr, locale } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const startTodayDailyLoop = useAppStore((state) => state.startTodayDailyLoop);
  const navigate = useNavigate();

  if (!dashboard?.dailyLoopPlan) {
    return (
      <Card>
        {tr("Подгружаю daily loop...")}
      </Card>
    );
  }

  const plan = dashboard.dailyLoopPlan;
  const journeyState = dashboard.journeyState;
  const coachMessage =
    locale === "ru"
      ? `Сегодняшний путь уже собран: сначала мы укрепим ${plan.focusArea}, а потом я объясню, как это изменит твой следующий шаг.`
      : `Today's route is already prepared: first we reinforce ${plan.focusArea}, then I explain how it changes your next step.`;
  const coachSupportingText =
    journeyState?.currentStrategySummary ?? plan.whyThisNow;
  const nextLoopStep =
    journeyState?.nextBestAction ?? plan.nextStepHint;
  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const skillTrajectory = journeyState?.strategySnapshot.skillTrajectory ?? null;
  const strategyMemory = journeyState?.strategySnapshot.strategyMemory ?? null;
  const routeCadenceMemory = journeyState?.strategySnapshot.routeCadenceMemory ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const ritualSignalMemory = journeyState?.strategySnapshot.ritualSignalMemory ?? null;
  const dayShape = describeRouteDayShape(plan, routeRecoveryMemory, routeReentryProgress, routeEntryMemory, tr);
  const ritualWindow = describeRitualWindow(ritualSignalMemory, tr);
  const taskDrivenInput = resolveTaskDrivenInputSurface(plan, journeyState ?? null, tr);
  const followUpHint = buildRouteFollowUpHintFromState(plan, journeyState ?? null, tr);
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const explainActions = [
    {
      id: "daily-loop-simpler",
      label: locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        plan.completedAt && tomorrowPreview
          ? locale === "ru"
            ? sessionSummary?.headline ?? `Сегодняшняя сессия уже завершена. Сейчас задача - не запускать её заново, а понять, как система переносит сигнал в завтрашний маршрут вокруг ${tomorrowPreview.focusArea}.`
            : sessionSummary?.headline ?? `Today's session is already complete. The goal now is not to rerun it, but to understand how the system carries the signal into tomorrow around ${tomorrowPreview.focusArea}.`
          : locale === "ru"
            ? `Сегодня у тебя одна собранная сессия вокруг ${plan.focusArea}: пройди её от начала до конца, и система обновит следующий шаг без распада на отдельные режимы.`
            : `Today you have one assembled session around ${plan.focusArea}: complete it end to end and the system will update the next step without falling into separate modes.`,
    },
    {
      id: "daily-loop-why",
      label: locale === "ru" ? "Почему именно это" : "Why this now",
      text:
        plan.completedAt && tomorrowPreview
          ? practiceShiftLine ?? routeCadenceMemory?.summary ?? tomorrowPreview.reason
          : routeRecoveryMemory?.summary ?? routeCadenceMemory?.summary ?? plan.whyThisNow,
    },
    {
      id: "daily-loop-priority",
      label: locale === "ru" ? "Что важнее всего" : "What matters most",
      text:
        plan.completedAt && sessionSummary
          ? practiceShiftLine ?? sessionSummary.watchSignal
          : plan.sessionKind === "diagnostic"
          ? locale === "ru"
            ? "Сейчас важнее всего пройти checkpoint честно и не пытаться выглядеть сильнее, чем есть, потому что от этого зависит точность следующего маршрута."
            : "What matters most right now is completing the checkpoint honestly rather than trying to look stronger than you are, because the next route depends on that precision."
          : locale === "ru"
            ? `Сейчас важнее всего удержать lead-focus ${plan.focusArea}, а не пытаться одинаково сильно тренировать всё сразу.`
            : `What matters most right now is keeping ${plan.focusArea} as the lead focus instead of trying to train everything equally at once.`,
    },
    {
      id: "daily-loop-next",
      label: locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: nextLoopStep,
    },
  ];

  async function handleStart() {
    await startTodayDailyLoop();
    navigate(routes.lessonRunner);
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Daily Loop")}
        title={plan.headline}
        description={plan.summary}
      />

      <LizaCoachPanel
        locale={locale}
        playKey={`daily-loop:${dashboard.profile.id}:${plan.id}:${plan.status}`}
        title={tr("Liza Daily Guidance")}
        message={coachMessage}
        replayCta={tr("Послушать план ещё раз")}
        supportingText={coachSupportingText}
      />

      <LizaGuidanceGrid
        currentLabel={locale === "ru" ? "Что сейчас происходит" : "What is happening now"}
        currentText={
          locale === "ru"
            ? `Система уже собрала для тебя ${dayShape.title.toLowerCase()}: ${plan.recommendedLessonTitle}, ${plan.estimatedMinutes} минут и ${plan.steps.length} связанных шагов.`
            : `The system has already prepared a ${dayShape.title.toLowerCase()} for today: ${plan.recommendedLessonTitle}, ${plan.estimatedMinutes} minutes, and ${plan.steps.length} connected steps.`
        }
        whyLabel={locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          locale === "ru"
            ? `${dayShape.summary}${ritualWindow ? ` ${ritualWindow.summary}` : ""} Этот loop строится вокруг ${plan.focusArea} и держит один объяснимый маршрут вместо разрозненных упражнений.`
            : `${dayShape.summary}${ritualWindow ? ` ${ritualWindow.summary}` : ""} This loop is built around ${plan.focusArea} and keeps one explainable route instead of disconnected exercises.`
        }
        nextLabel={locale === "ru" ? "Что делать дальше" : "What to do next"}
        nextText={nextLoopStep}
      />

      <LizaExplainActions
        title={locale === "ru" ? "Разобрать план с Лизой" : "Break down the plan with Liza"}
        actions={explainActions}
      />

      <DailyRitualPanel plan={plan} tr={tr} />

      <div className="grid gap-4 xl:grid-cols-[1.12fr_0.88fr]">
        <Card className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-xs uppercase tracking-[0.22em] text-coral">{tr("Today")}</div>
              <div className="mt-2 text-2xl font-semibold text-ink">{plan.recommendedLessonTitle}</div>
            </div>
            <div className="rounded-[22px] bg-white/75 px-4 py-3 text-sm text-slate-700">
              {`${plan.estimatedMinutes} ${tr("minutes")}`}
            </div>
          </div>

          <div className="rounded-[24px] bg-sand/70 p-4 text-sm leading-6 text-slate-700">
            {plan.whyThisNow}
          </div>

          <div className="rounded-[24px] border border-white/70 bg-white/80 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{tr("Day shape")}</div>
                <div className="mt-2 text-lg font-semibold text-ink">{dayShape.title}</div>
                {dayShape.substageLabel ? (
                  <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-coral">
                    {dayShape.substageLabel}
                  </div>
                ) : null}
                {dayShape.expansionStageLabel ? (
                  <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent">
                    {dayShape.expansionStageLabel}
                  </div>
                ) : null}
              </div>
              <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
                {dayShape.compactnessLabel}
              </div>
            </div>
            <div className="mt-3 text-sm leading-6 text-slate-700">{dayShape.summary}</div>
            {dayShape.expansionWindowLabel ? (
              <div className="mt-3 text-xs text-slate-500">{dayShape.expansionWindowLabel}</div>
            ) : null}
          </div>

          {ritualWindow ? (
            <div className="rounded-[24px] border border-coral/15 bg-coral/6 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-coral">{tr("Ritual arc")}</div>
                  <div className="mt-2 text-lg font-semibold text-ink">{ritualWindow.title}</div>
                </div>
                {ritualWindow.windowLabel ? (
                  <div className="rounded-full bg-white/76 px-3 py-1 text-xs font-semibold text-coral">
                    {ritualWindow.windowLabel}
                  </div>
                ) : null}
              </div>
              <div className="mt-3 text-sm leading-6 text-slate-700">{ritualWindow.summary}</div>
              {ritualWindow.hint ? (
                <div className="mt-3 rounded-[18px] bg-white/76 p-3 text-sm text-slate-700">{ritualWindow.hint}</div>
              ) : null}
            </div>
          ) : null}

          {skillTrajectory ? (
            <div className="rounded-[24px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">{tr("Multi-day memory")}:</span> {skillTrajectory.summary}
            </div>
          ) : null}
      {strategyMemory ? (
        <div className="rounded-[24px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Long strategy memory")}:</span> {strategyMemory.summary}
        </div>
      ) : null}
      {routeCadenceMemory ? (
        <div className="rounded-[24px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Route cadence")}:</span> {routeCadenceMemory.summary}
        </div>
      ) : null}
      {routeRecoveryMemory ? (
        <div className="rounded-[24px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
          <span className="font-semibold text-ink">{tr("Recovery arc")}:</span> {routeRecoveryMemory.summary}
        </div>
      ) : null}

          <div className="space-y-3">
            {plan.steps.map((step, index) => (
              <div
                key={step.id}
                className="rounded-[24px] border border-white/70 bg-white/78 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-ink">{`${index + 1}. ${step.title}`}</div>
                  <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
                    {`${step.durationMinutes} ${tr("min")}`}
                  </div>
                </div>
                <div className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-400">{step.skill}</div>
                <div className="mt-3 text-sm leading-6 text-slate-700">{step.description}</div>
              </div>
            ))}
          </div>

          {taskDrivenInput ? (
            <div className="rounded-[24px] border border-accent/15 bg-accent/8 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Task-driven input")}</div>
              <div className="mt-2 text-lg font-semibold text-ink">{taskDrivenInput.title}</div>
              <div className="mt-3 text-sm leading-6 text-slate-700">{taskDrivenInput.summary}</div>
              <div className="mt-3 rounded-[18px] bg-white/76 p-3 text-sm text-slate-700">{taskDrivenInput.bridge}</div>
              <div className="mt-3 flex flex-wrap gap-3">
                <Link to={taskDrivenInput.route} className="proof-lesson-primary-button">
                  {taskDrivenInput.title}
                </Link>
                <Link to={routes.lessonRunner} className="proof-lesson-secondary-action">
                  {tr("Skip to guided route")}
                </Link>
              </div>
            </div>
          ) : null}
        </Card>

        <div className="space-y-4">
          <Card className="space-y-4">
            <div className="text-lg font-semibold text-ink">{tr("Next best action")}</div>
            <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
              {plan.nextStepHint}
            </div>
            <div className="flex flex-wrap gap-3">
              <Button type="button" onClick={() => void handleStart()}>
                {plan.lessonRunId ? tr("Resume today’s loop") : tr("Start today’s loop")}
              </Button>
              <Link to={routes.dashboard} className="proof-lesson-secondary-action">
                {tr("Back to dashboard")}
              </Link>
            </div>
          </Card>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Session logic")}</div>
            <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
              {locale === "ru"
                ? `Этот loop использует режим ${plan.preferredMode} и бюджет ${plan.timeBudgetMinutes} минут, чтобы связать recommendation, practice и следующий шаг в один сценарий.`
                : `This loop uses ${plan.preferredMode} mode and a ${plan.timeBudgetMinutes}-minute budget to connect recommendation, practice, and the next step into one scenario.`}
            </div>
            <div className="rounded-[22px] bg-white/76 p-4 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">{tr("Route shape")}:</span> {dayShape.summary}
            </div>
            {dayShape.expansionStageLabel ? (
              <div className="rounded-[22px] bg-accent/8 p-4 text-sm leading-6 text-slate-700">
                <span className="font-semibold text-ink">{tr("Expansion stage")}:</span> {dayShape.expansionStageLabel}
                {dayShape.expansionWindowLabel ? ` · ${dayShape.expansionWindowLabel}` : ""}
              </div>
            ) : null}
            {followUpHint ? (
              <div className="rounded-[22px] bg-accent/8 p-4 text-sm leading-6 text-slate-700">
                <span className="font-semibold text-ink">{tr("What comes next")}:</span> {followUpHint}
              </div>
            ) : null}
            {plan.completedAt && sessionSummary ? (
              <JourneySessionSummaryPanel
                summary={sessionSummary}
                title={tr("Session shift")}
                tr={tr}
              />
            ) : null}
            {plan.completedAt && tomorrowPreview ? (
              <div className="rounded-[22px] border border-accent/20 bg-accent/8 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Tomorrow preview")}</div>
                <div className="mt-2 text-base font-semibold text-ink">{tomorrowPreview.headline}</div>
                <div className="mt-3 text-sm leading-6 text-slate-700">{tomorrowPreview.reason}</div>
                {practiceShiftLine ? (
                  <div className="mt-3 rounded-[18px] bg-white/76 p-3 text-sm text-slate-700">
                    <span className="font-semibold text-ink">{tr("Practice shift")}:</span> {practiceShiftLine}
                  </div>
                ) : null}
              </div>
            ) : null}
            {plan.completedAt ? (
              <div className="rounded-[22px] bg-accent/10 p-4 text-sm leading-6 text-accent">
                {journeyState?.nextBestAction ?? tr("This daily loop is already completed. Open the dashboard to see the updated next step.")}
              </div>
            ) : null}
          </Card>
        </div>
      </div>
    </div>
  );
}

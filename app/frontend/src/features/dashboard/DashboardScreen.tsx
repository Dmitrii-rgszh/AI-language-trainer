import { Link, useLocation } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { DashboardDailyLoopSection } from "./DashboardDailyLoopSection";
import { DashboardRouteContinuitySection } from "./DashboardRouteContinuitySection";
import { DashboardResumeLessonSection } from "./DashboardResumeLessonSection";
import { DashboardWeakSpotsAndActionsSection } from "./DashboardWeakSpotsAndActionsSection";
import { useDashboardScreen } from "./useDashboardScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";

function formatRussianStepCount(value: number) {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `${value} шаг`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${value} шага`;
  }
  return `${value} шагов`;
}

export function DashboardScreen() {
  const dashboardView = useDashboardScreen();
  const location = useLocation();

  if (!dashboardView.dashboard) {
    return <Card>{dashboardView.tr("Подгружаю dashboard...")}</Card>;
  }

  const locationState = (location.state ?? null) as {
    routeEntrySource?: string;
  } | null;
  const isOnboardingBridge = locationState?.routeEntrySource === "onboarding_completion";
  const isResultsBridge = locationState?.routeEntrySource === "results_to_dashboard";
  const resumeLesson = dashboardView.dashboard.resumeLesson;
  const hasResumeLesson = Boolean(resumeLesson);
  const dailyLoopPlan = dashboardView.dashboard.dailyLoopPlan;
  const completedResumeSteps = resumeLesson
    ? Math.min(resumeLesson.completedBlocks, resumeLesson.totalBlocks)
    : 0;
  const completedResumeStepsText =
    dashboardView.locale === "ru"
      ? completedResumeSteps === 1
        ? "и прошёл первый шаг"
        : completedResumeSteps > 1
          ? `и прошёл ${formatRussianStepCount(completedResumeSteps)}`
          : ""
      : completedResumeSteps === 1
        ? "and completed the first step"
        : completedResumeSteps > 1
          ? `and completed ${completedResumeSteps} steps`
          : "";

  const weakestSpotTitle = dashboardView.dashboard.weakSpots[0]?.title;
  const afterLessonPreview =
    weakestSpotTitle
      ? dashboardView.locale === "ru"
        ? `повторим «${dashboardView.tr(weakestSpotTitle)}»`
        : `a short reinforcement around “${dashboardView.tr(weakestSpotTitle)}”`
      : dailyLoopPlan
        ? dashboardView.locale === "ru"
          ? `попробуем «${dashboardView.tr(dailyLoopPlan.focusArea)}»`
          : `the next step around “${dashboardView.tr(dailyLoopPlan.focusArea)}”`
        : null;
  const coachMessage =
    (hasResumeLesson
      ? dashboardView.locale === "ru"
        ? `Ты уже начал этот урок${completedResumeStepsText ? ` ${completedResumeStepsText}` : ""}. Давай просто закончим его сейчас.`
        : "You already have an unfinished lesson open. Just continue it, and after completion I will show the updated next step."
      : isOnboardingBridge
      ? dashboardView.locale === "ru"
        ? "Первый личный маршрут уже готов. Начни с сегодняшнего шага, и я мягко переведу тебя дальше."
        : "Your first personal route is ready. Start with today's step and I will gently guide you forward."
      : isResultsBridge
        ? dashboardView.locale === "ru"
          ? "Маршрут уже обновлён после последней сессии. Здесь нужен только следующий шаг, без перегруза."
          : "The route is already updated after the last session. You only need the next step here, not the full overload."
      : dashboardView.locale === "ru"
        ? "Я уже собрала для тебя следующий шаг. Сначала открой сегодняшний маршрут, а потом закрепи один самый важный сигнал."
        : "I have already prepared your next step. Open today's route first, then reinforce the single most important signal.");
  const coachSpokenMessage =
    hasResumeLesson
      ? dashboardView.locale === "ru"
        ? `Ты уже начал этот урок${completedResumeStepsText ? ` ${completedResumeStepsText}` : ""}. Давай просто закончим его сейчас.`
        : `You already have an unfinished lesson open. Just continue it first. After it ends, I will assemble the next step for you.`
    : isOnboardingBridge
      ? dashboardView.locale === "ru"
        ? `Первый личный маршрут уже готов. Начни с сегодняшнего шага, и я проведу тебя дальше.`
        : `Your first personal route is ready. Start with today's step and I will guide you forward.`
      : isResultsBridge
        ? dashboardView.locale === "ru"
          ? `Маршрут уже обновлён после последней сессии. Посмотри на следующий шаг и продолжай путь.`
          : `The route is already updated after the last session. Review the next step and continue the route.`
      : dashboardView.locale === "ru"
      ? `Я уже собрала для тебя следующий шаг. Начни с сегодняшнего маршрута, а потом закрепи ${
          weakestSpotTitle ? `слабое место ${weakestSpotTitle}` : "один слабый сигнал"
        }.`
      : `I have already prepared your next step. Start with today's route, then reinforce ${
          weakestSpotTitle ? `your weak spot ${weakestSpotTitle}` : "one weak signal"
        }.`;
  const coachSupportingText =
    (hasResumeLesson
      ? dashboardView.locale === "ru"
        ? null
        : `The current block “${dashboardView.tr(dashboardView.dashboard.resumeLesson?.currentBlockTitle ?? "current block")}” is already open. Just return to the lesson and finish it calmly.`
      : isOnboardingBridge
      ? dashboardView.locale === "ru"
        ? "Маршрут уже собран, continuity сохранена, а следующий шаг не нужно искать вручную."
        : "The route is already assembled, continuity is preserved, and the next step does not need to be found manually."
      : isResultsBridge
        ? dashboardView.locale === "ru"
          ? "После прошлой сессии здесь уже ждёт следующий шаг."
          : "This screen is already built from the last session result: what matters here is a gentle entry into the next step."
      : null) ??
    (dashboardView.locale === "ru"
      ? dailyLoopPlan
        ? `Сейчас у тебя один ясный шаг: ${dashboardView.tr(dailyLoopPlan.focusArea)}, ${dailyLoopPlan.estimatedMinutes} мин. После него я покажу, что делать дальше.`
        : "Здесь я показываю только следующий нужный шаг, без перегруза и без лишних ответвлений."
      : "I only show what matters for the next step here, without overloading the screen.");

  return (
    <div className="space-y-4">
      <LivingDepthSection id={livingDepthSectionIds.dashboardResume}>
        <LizaCoachPanel
          locale={dashboardView.locale}
          playKey={`dashboard:${dashboardView.dashboard.profile.id}:${dashboardView.dashboard.recommendation.id}:${weakestSpotTitle ?? "stable"}`}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={dashboardView.locale}
          replayCta={dashboardView.tr("Послушать ещё раз")}
          primaryAction={
            hasResumeLesson ? (
              <div className="space-y-2">
                <div className="text-sm font-semibold text-accent">{dashboardView.tr("Let's finish")}</div>
                <Button
                  type="button"
                  onClick={dashboardView.openLessonRunner}
                  className="proof-lesson-primary-button px-7 py-3.5 text-base"
                >
                  {dashboardView.tr("Resume lesson")}
                </Button>
                <div className="text-xs font-semibold text-slate-500">
                  {dashboardView.tr("You will continue from this exact place")}
                </div>
              </div>
            ) : (
              <Button
                type="button"
                onClick={() => void dashboardView.handleStartLesson()}
                className="proof-lesson-primary-button px-7 py-3.5 text-base"
              >
                {dashboardView.primaryRouteLabel}
              </Button>
            )
          }
          secondaryAction={hasResumeLesson ? undefined : (
            <Link
              to={routes.progress}
              className="proof-lesson-secondary-action"
            >
              {dashboardView.tr("Открыть прогресс")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      {hasResumeLesson ? (
        <>
          <LivingDepthSection id={livingDepthSectionIds.dashboardResume}>
            <DashboardResumeLessonSection
              onDiscardLessonRun={dashboardView.handleDiscardLessonRun}
              onRestartLesson={dashboardView.handleRestartLesson}
              onResumeLesson={dashboardView.openLessonRunner}
              resumeLesson={dashboardView.dashboard.resumeLesson}
              showPrimaryAction={false}
              tr={dashboardView.tr}
            />
          </LivingDepthSection>
          {afterLessonPreview ? (
            <Card className="space-y-3 border border-accent/12 bg-white/70 shadow-none">
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-coral">
                {dashboardView.tr("After you finish")}
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-[22px] bg-white/72 p-4 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">→</span> {afterLessonPreview}
                </div>
                <div className="rounded-[22px] bg-white/72 p-4 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">→</span>{" "}
                  {dashboardView.tr("we will try saying it out loud")}
                </div>
              </div>
            </Card>
          ) : null}
        </>
      ) : (
        <>
          <DashboardRouteContinuitySection
            dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
            journeyState={dashboardView.dashboard.journeyState}
            onStartDailyLoop={dashboardView.handleStartDailyLoop}
            showActions={false}
            tr={dashboardView.tr}
          />

          <LivingDepthSection id={livingDepthSectionIds.dashboardDailyLoop}>
            <DashboardDailyLoopSection
              dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
              journeyState={dashboardView.dashboard.journeyState}
              tr={dashboardView.tr}
            />
          </LivingDepthSection>
        </>
      )}

      <LivingDepthSection id={livingDepthSectionIds.dashboardActions}>
        <DashboardWeakSpotsAndActionsSection
          quickActions={dashboardView.extendedQuickActions}
          tr={dashboardView.tr}
          tt={dashboardView.tt}
          weakSpots={dashboardView.dashboard.weakSpots}
        />
      </LivingDepthSection>
    </div>
  );
}

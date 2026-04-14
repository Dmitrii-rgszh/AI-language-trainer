import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { Card } from "../../shared/ui/Card";
import { DashboardAdaptiveLoopSection } from "./DashboardAdaptiveLoopSection";
import { DashboardDailyLoopSection } from "./DashboardDailyLoopSection";
import { DashboardHeroSection } from "./DashboardHeroSection";
import { DashboardRecentActivitySection } from "./DashboardRecentActivitySection";
import { DashboardRouteContinuitySection } from "./DashboardRouteContinuitySection";
import { DashboardResumeLessonSection } from "./DashboardResumeLessonSection";
import { DashboardRoadmapSection } from "./DashboardRoadmapSection";
import { DashboardSignalsSection } from "./DashboardSignalsSection";
import { DashboardWeakSpotsAndActionsSection } from "./DashboardWeakSpotsAndActionsSection";
import { useDashboardScreen } from "./useDashboardScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { RouteIntelligencePanel } from "../../widgets/journey/RouteIntelligencePanel";

export function DashboardScreen() {
  const dashboardView = useDashboardScreen();

  if (!dashboardView.dashboard) {
    return <Card>{dashboardView.tr("Подгружаю dashboard...")}</Card>;
  }

  const weakestSpotTitle = dashboardView.dashboard.weakSpots[0]?.title;
  const coachMessage =
    dashboardView.tr("Я уже собрала для тебя следующий шаг: начни с сегодняшнего маршрута, а потом закрепи один слабый сигнал, чтобы прогресс шёл как единая система.") +
    (dashboardView.recommendationGoal ? ` ${dashboardView.recommendationGoal}` : "");
  const coachSpokenMessage =
    dashboardView.locale === "ru"
      ? `Я уже собрала для тебя следующий шаг. Начни с сегодняшнего маршрута, а потом закрепи ${
          weakestSpotTitle ? `слабое место ${weakestSpotTitle}` : "один слабый сигнал"
        }, чтобы прогресс шёл как единая система.`
      : `I have already prepared your next step. Start with today's route, then reinforce ${
          weakestSpotTitle ? `your weak spot ${weakestSpotTitle}` : "one weak signal"
        } so your progress keeps moving as one connected system.`;
  const coachSupportingText =
    dashboardView.locale === "ru"
      ? "Лиза уже начинает жить не только в пробном уроке: теперь она помогает связать твой roadmap, следующие действия и слабые сигналы прямо на dashboard."
      : "Liza is no longer limited to the proof lesson. She now helps connect your roadmap, next actions, and weak signals directly on the dashboard.";
  const currentFocusArea =
    dashboardView.dashboard.journeyState?.currentFocusArea ??
    dashboardView.dashboard.dailyLoopPlan?.focusArea ??
    dashboardView.dashboard.studyLoop?.focusArea ??
    "dashboard";
  const tomorrowPreview = dashboardView.dashboard.journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = dashboardView.dashboard.journeyState?.strategySnapshot.sessionSummary ?? null;
  const hasCompletedToday = dashboardView.dashboard.dailyLoopPlan?.completedAt !== null;
  const hasActiveSession = dashboardView.dashboard.resumeLesson !== null;
  const nextBestText =
    hasActiveSession
      ? dashboardView.locale === "ru"
        ? "У тебя уже есть активная сессия. Самый сильный следующий шаг сейчас - вернуться в неё, а не переключаться на новый модуль."
        : "You already have an active session. The strongest next step right now is to return to it instead of switching to a new module."
      : dashboardView.dashboard.journeyState?.nextBestAction ??
        dashboardView.dashboard.dailyLoopPlan?.nextStepHint ??
        dashboardView.tr("Start the recommended lesson and keep the route moving.");
  const explainActions = [
    {
      id: "dashboard-simpler",
      label: dashboardView.locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        dashboardView.locale === "ru"
          ? hasCompletedToday && tomorrowPreview
            ? sessionSummary?.headline ?? `Сегодняшний маршрут уже закрыт. Сейчас тебе не нужно начинать новый блок, а нужно понять, как система готовит завтрашний шаг вокруг ${tomorrowPreview.focusArea}.`
            : `Сейчас у тебя один главный маршрут: открой ${dashboardView.dashboard.dailyLoopPlan ? "daily loop" : "рекомендуемый урок"}, укрепи фокус ${currentFocusArea} и затем посмотри обновлённый следующий шаг.`
          : hasCompletedToday && tomorrowPreview
            ? sessionSummary?.headline ?? `Today's route is already complete. You do not need another random block now. You need to understand how the system is shaping tomorrow around ${tomorrowPreview.focusArea}.`
            : `You have one main route right now: open the ${dashboardView.dashboard.dailyLoopPlan ? "daily loop" : "recommended lesson"}, reinforce ${currentFocusArea}, then review the updated next step.`,
    },
    {
      id: "dashboard-why",
      label: dashboardView.locale === "ru" ? "Почему именно это" : "Why this now",
      text:
        hasCompletedToday && tomorrowPreview
          ? sessionSummary?.whatWorked ?? tomorrowPreview.reason
          : dashboardView.dashboard.dailyLoopPlan?.whyThisNow ??
        dashboardView.recommendationGoal ??
        coachSupportingText,
    },
    {
      id: "dashboard-priority",
      label: dashboardView.locale === "ru" ? "Что важнее всего" : "What matters most",
      text:
        hasCompletedToday && sessionSummary
          ? sessionSummary.watchSignal
          : dashboardView.dashboard.recommendation.lessonType === "recovery"
          ? dashboardView.locale === "ru"
            ? "Сейчас важнее всего не ширина, а восстановление: сначала снять повторяющийся слабый сигнал, а уже потом расширять маршрут."
            : "What matters most right now is not breadth but recovery: stabilize the repeating weak signal first, then widen the route."
          : dashboardView.dashboard.dailyLoopPlan?.sessionKind === "diagnostic"
            ? dashboardView.locale === "ru"
              ? "Сейчас важнее всего точность маршрута. Короткий checkpoint даст системе более честный и полезный следующий шаг."
              : "What matters most right now is route precision. A short checkpoint will give the system a more honest and useful next step."
            : dashboardView.locale === "ru"
              ? `Сейчас важнее всего не распыляться: держать один lead-signal вокруг ${currentFocusArea} и использовать weak spots как уточнение, а не как список отдельных тревог.`
              : `What matters most right now is not to scatter your effort: keep one lead signal around ${currentFocusArea} and use weak spots as refinement, not as a list of separate worries.`,
    },
    {
      id: "dashboard-next",
      label: dashboardView.locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: hasCompletedToday && sessionSummary ? sessionSummary.strategyShift : nextBestText,
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={dashboardView.tr("Dashboard")}
        title={`${dashboardView.tr("Welcome back")}, ${dashboardView.dashboard.profile.name}`}
        description={dashboardView.tr("Choose the next lesson, review weak spots, and keep the daily rhythm moving.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.dashboardCoach}>
        <LizaCoachPanel
          locale={dashboardView.locale}
          playKey={`dashboard:${dashboardView.dashboard.profile.id}:${dashboardView.dashboard.recommendation.id}:${weakestSpotTitle ?? "stable"}`}
          title={dashboardView.tr("Liza Coach Layer")}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={dashboardView.locale}
          replayCta={dashboardView.tr("Послушать ещё раз")}
          primaryAction={(
            <Button type="button" onClick={() => void dashboardView.handleStartLesson()} className="proof-lesson-primary-button">
              {dashboardView.primaryRouteLabel}
            </Button>
          )}
          secondaryAction={(
            <Link to={routes.pronunciation} className="proof-lesson-secondary-action">
              {dashboardView.tr("Открыть pronunciation lab")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <LizaExplainActions
        title={dashboardView.locale === "ru" ? "Liza explain-actions" : "Liza explain-actions"}
        actions={explainActions}
      />

      <DashboardRouteContinuitySection
        dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
        journeyState={dashboardView.dashboard.journeyState}
        onStartDailyLoop={dashboardView.handleStartDailyLoop}
        tr={dashboardView.tr}
      />

      <LivingDepthSection id={livingDepthSectionIds.dashboardDailyLoop}>
        <DashboardDailyLoopSection
          dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
          journeyState={dashboardView.dashboard.journeyState}
          onStartDailyLoop={dashboardView.handleStartDailyLoop}
          tr={dashboardView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardHero}>
        <DashboardHeroSection
          dailyGoalProgress={dashboardView.dailyGoalProgress}
          dashboard={dashboardView.dashboard}
          disabledProviders={dashboardView.disabledProviders}
          fallbackProviders={dashboardView.fallbackProviders}
          onStartLesson={dashboardView.handleStartLesson}
          primaryRouteLabel={dashboardView.primaryRouteLabel}
          readyProviders={dashboardView.readyProviders}
          recommendationGoal={dashboardView.recommendationGoal ?? ""}
          recoveringSignals={dashboardView.recoveringSignals}
          tl={dashboardView.tl}
          totalProviders={dashboardView.totalProviders}
          tr={dashboardView.tr}
        />
      </LivingDepthSection>

      <RouteIntelligencePanel
        dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
        journeyState={dashboardView.dashboard.journeyState}
        title={dashboardView.tr("Route intelligence")}
        tr={dashboardView.tr}
      />

      <LivingDepthSection id={livingDepthSectionIds.dashboardRoadmap}>
        <DashboardRoadmapSection
          diagnosticRoadmap={dashboardView.diagnosticRoadmap}
          onStartDiagnosticCheckpoint={dashboardView.handleStartDiagnosticCheckpoint}
          onStartRecoveryLesson={dashboardView.handleStartRecoveryLesson}
          roadmapSummary={dashboardView.roadmapSummary}
          tr={dashboardView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardResume}>
        <DashboardResumeLessonSection
          onDiscardLessonRun={dashboardView.handleDiscardLessonRun}
          onRestartLesson={dashboardView.handleRestartLesson}
          onResumeLesson={dashboardView.openLessonRunner}
          resumeLesson={dashboardView.dashboard.resumeLesson}
          tr={dashboardView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardActions}>
        <DashboardWeakSpotsAndActionsSection
          quickActions={dashboardView.extendedQuickActions}
          tr={dashboardView.tr}
          tt={dashboardView.tt}
          weakSpots={dashboardView.dashboard.weakSpots}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardLoop}>
        <DashboardAdaptiveLoopSection
          adaptiveHeadline={dashboardView.adaptiveHeadline}
          adaptiveSummary={dashboardView.adaptiveSummary}
          dailyLoopPlan={dashboardView.dashboard.dailyLoopPlan}
          onStartDailyRoute={dashboardView.handleStartLesson}
          onReviewVocabulary={dashboardView.handleVocabularyReview}
          onStartRecoveryLesson={dashboardView.handleStartRecoveryLesson}
          primaryRouteLabel={dashboardView.primaryRouteLabel}
          reviewingVocabularyId={dashboardView.reviewingVocabularyId}
          studyLoop={dashboardView.dashboard.studyLoop}
          tr={dashboardView.tr}
          tt={dashboardView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardSignals}>
        <DashboardSignalsSection
          progress={dashboardView.dashboard.progress}
          studyLoop={dashboardView.dashboard.studyLoop}
          tr={dashboardView.tr}
          tt={dashboardView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.dashboardActivity}>
        <DashboardRecentActivitySection
          activityError={dashboardView.activityError}
          events={dashboardView.recentActivity}
          formatDateTime={dashboardView.formatDateTime}
          providers={dashboardView.providers}
          tr={dashboardView.tr}
          tt={dashboardView.tt}
        />
      </LivingDepthSection>
    </div>
  );
}

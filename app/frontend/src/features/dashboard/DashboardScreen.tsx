import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { Card } from "../../shared/ui/Card";
import { DashboardAdaptiveLoopSection } from "./DashboardAdaptiveLoopSection";
import { DashboardHeroSection } from "./DashboardHeroSection";
import { DashboardRecentActivitySection } from "./DashboardRecentActivitySection";
import { DashboardResumeLessonSection } from "./DashboardResumeLessonSection";
import { DashboardRoadmapSection } from "./DashboardRoadmapSection";
import { DashboardSignalsSection } from "./DashboardSignalsSection";
import { DashboardWeakSpotsAndActionsSection } from "./DashboardWeakSpotsAndActionsSection";
import { useDashboardScreen } from "./useDashboardScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";

export function DashboardScreen() {
  const dashboardView = useDashboardScreen();

  if (!dashboardView.dashboard) {
    return <Card>{dashboardView.tr("Подгружаю dashboard...")}</Card>;
  }

  const weakestSpotTitle = dashboardView.dashboard.weakSpots[0]?.title;
  const coachMessage =
    dashboardView.tr("Я уже собрала для тебя следующий шаг: начни с рекомендованного урока, а потом закрепи один слабый сигнал, чтобы прогресс шёл как единая система.") +
    (dashboardView.recommendationGoal ? ` ${dashboardView.recommendationGoal}` : "");
  const coachSpokenMessage =
    dashboardView.locale === "ru"
      ? `Я уже собрала для тебя следующий шаг. Начни с рекомендованного урока, а потом закрепи ${
          weakestSpotTitle ? `слабое место ${weakestSpotTitle}` : "один слабый сигнал"
        }, чтобы прогресс шёл как единая система.`
      : `I have already prepared your next step. Start with the recommended lesson, then reinforce ${
          weakestSpotTitle ? `your weak spot ${weakestSpotTitle}` : "one weak signal"
        } so your progress keeps moving as one connected system.`;
  const coachSupportingText =
    dashboardView.locale === "ru"
      ? "Лиза уже начинает жить не только в пробном уроке: теперь она помогает связать твой roadmap, следующие действия и слабые сигналы прямо на dashboard."
      : "Liza is no longer limited to the proof lesson. She now helps connect your roadmap, next actions, and weak signals directly on the dashboard.";

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
              {dashboardView.tr("Начать рекомендуемый урок")}
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

      <LivingDepthSection id={livingDepthSectionIds.dashboardHero}>
        <DashboardHeroSection
          dailyGoalProgress={dashboardView.dailyGoalProgress}
          dashboard={dashboardView.dashboard}
          disabledProviders={dashboardView.disabledProviders}
          fallbackProviders={dashboardView.fallbackProviders}
          onStartLesson={dashboardView.handleStartLesson}
          readyProviders={dashboardView.readyProviders}
          recommendationGoal={dashboardView.recommendationGoal ?? ""}
          recoveringSignals={dashboardView.recoveringSignals}
          tl={dashboardView.tl}
          totalProviders={dashboardView.totalProviders}
          tr={dashboardView.tr}
        />
      </LivingDepthSection>

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
          onReviewVocabulary={dashboardView.handleVocabularyReview}
          onStartRecoveryLesson={dashboardView.handleStartRecoveryLesson}
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

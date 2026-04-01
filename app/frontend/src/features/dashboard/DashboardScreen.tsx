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

export function DashboardScreen() {
  const dashboardView = useDashboardScreen();

  if (!dashboardView.dashboard) {
    return <Card>{dashboardView.tr("Подгружаю dashboard...")}</Card>;
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={dashboardView.tr("Dashboard")}
        title={`${dashboardView.tr("Welcome back")}, ${dashboardView.dashboard.profile.name}`}
        description={dashboardView.tr("Choose the next lesson, review weak spots, and keep the daily rhythm moving.")}
      />

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

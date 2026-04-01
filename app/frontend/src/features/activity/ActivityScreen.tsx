import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { ActivityHistorySection } from "./ActivityHistorySection";
import { ActivityOverviewSection } from "./ActivityOverviewSection";
import { ActivitySignalsSection } from "./ActivitySignalsSection";
import { ActivityStudyLoopSection } from "./ActivityStudyLoopSection";
import { useActivityScreen } from "./useActivityScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

export function ActivityScreen() {
  const activityView = useActivityScreen();

  if (!activityView.progress) {
    return <Card>{activityView.tr("Подгружаю activity...")}</Card>;
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={activityView.tr("Activity")}
        title={activityView.tr("Unified Activity And History")}
        description={activityView.tr("One timeline for lessons, speaking practice, listening signals, and result history.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.activityOverview}>
        <ActivityOverviewSection
          lastLessonResult={activityView.lastLessonResult}
          mistakesCount={activityView.mistakes.length}
          progress={activityView.progress}
          pronunciationTrend={activityView.pronunciationTrend}
          speakingAttemptsCount={activityView.speakingAttempts.length}
          tr={activityView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.activityLoop}>
        <ActivityStudyLoopSection
          onReviewVocabulary={activityView.handleVocabularyReview}
          onStartRecoveryLesson={activityView.handleStartRecoveryLesson}
          reviewingVocabularyId={activityView.reviewingVocabularyId}
          studyLoop={activityView.studyLoop}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.activitySignals}>
        <ActivitySignalsSection
          formatDays={activityView.formatDays}
          listeningTrend={activityView.listeningTrend}
          studyLoop={activityView.studyLoop}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.activityHistory}>
        <ActivityHistorySection
          activityError={activityView.activityError}
          events={activityView.recentEvents}
          formatDateTime={activityView.formatDateTime}
          topMistakes={activityView.topMistakes}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>
    </div>
  );
}

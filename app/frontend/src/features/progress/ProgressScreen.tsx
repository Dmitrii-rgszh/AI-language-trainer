import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { ProgressDiagnosticSection } from "./ProgressDiagnosticSection";
import { ProgressHistorySection } from "./ProgressHistorySection";
import { ProgressOverviewSection } from "./ProgressOverviewSection";
import { ProgressPronunciationSection } from "./ProgressPronunciationSection";
import { ProgressSignalsSection } from "./ProgressSignalsSection";
import { useProgressScreen } from "./useProgressScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

export function ProgressScreen() {
  const progressView = useProgressScreen();

  if (!progressView.progress) {
    return <Card>{progressView.tr("Подгружаю progress...")}</Card>;
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={progressView.tr("Progress")}
        title={progressView.tr("Skill Progress")}
        description={progressView.tr("Follow your scores, recent practice, and roadmap shifts in one view.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.progressDiagnostic}>
        <ProgressDiagnosticSection
          diagnosticRoadmap={progressView.diagnosticRoadmap}
          onStartCheckpoint={progressView.handleStartCheckpoint}
          roadmapSummary={progressView.roadmapSummary}
          tl={progressView.tl}
          tr={progressView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressOverview}>
        <ProgressOverviewSection
          averageLessonScore={progressView.averageLessonScore}
          dailyGoalProgress={progressView.dailyGoalProgress}
          formatDate={progressView.formatDate}
          formatDays={progressView.formatDays}
          mostRecentLesson={progressView.mostRecentLesson}
          progress={progressView.progress}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressPronunciation}>
        <ProgressPronunciationSection
          progress={progressView.progress}
          pronunciationTrend={progressView.pronunciationTrend}
          tr={progressView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressHistory}>
        <ProgressHistorySection
          activityError={progressView.activityError}
          feedbackSourceLabel={progressView.feedbackSourceLabel}
          formatDate={progressView.formatDate}
          formatDateTime={progressView.formatDateTime}
          progress={progressView.progress}
          recentSpeakingAttempts={progressView.recentSpeakingAttempts}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressSignals}>
        <ProgressSignalsSection
          formatDays={progressView.formatDays}
          listeningAttempts={progressView.listeningAttempts}
          listeningTrend={progressView.listeningTrend}
          studyLoop={progressView.studyLoop}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>
    </div>
  );
}

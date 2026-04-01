import type { ResumeLessonCard } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardResumeLessonSectionProps = {
  onDiscardLessonRun: () => Promise<void>;
  onRestartLesson: () => Promise<void>;
  onResumeLesson: () => void;
  resumeLesson: ResumeLessonCard | null;
  tr: (value: string) => string;
};

export function DashboardResumeLessonSection({
  onDiscardLessonRun,
  onRestartLesson,
  onResumeLesson,
  resumeLesson,
  tr,
}: DashboardResumeLessonSectionProps) {
  if (!resumeLesson) {
    return null;
  }

  return (
    <Card className="space-y-4">
      <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Resume lesson")}</div>
      <div className="text-2xl font-semibold text-ink">{tr(resumeLesson.title)}</div>
      <div className="text-sm text-slate-600">
        {tr("Current block")}: {tr(resumeLesson.currentBlockTitle)}
      </div>
      <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
        {tr("Progress")}: {resumeLesson.completedBlocks}/{resumeLesson.totalBlocks} {tr("blocks completed")}.
      </div>
      <div className="flex flex-wrap gap-3">
        <Button onClick={onResumeLesson}>{tr("Resume lesson")}</Button>
        <Button variant="secondary" onClick={() => void onRestartLesson()}>
          {tr("Restart lesson")}
        </Button>
        <Button variant="ghost" onClick={() => void onDiscardLessonRun()}>
          {tr("Discard draft")}
        </Button>
      </div>
    </Card>
  );
}

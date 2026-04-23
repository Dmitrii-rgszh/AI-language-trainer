import type { ResumeLessonCard } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardResumeLessonSectionProps = {
  onDiscardLessonRun: () => Promise<void>;
  onRestartLesson: () => Promise<void>;
  onResumeLesson: () => void;
  resumeLesson: ResumeLessonCard | null;
  showPrimaryAction?: boolean;
  tr: (value: string) => string;
};

export function DashboardResumeLessonSection({
  onDiscardLessonRun,
  onRestartLesson,
  onResumeLesson,
  resumeLesson,
  showPrimaryAction = true,
  tr,
}: DashboardResumeLessonSectionProps) {
  if (!resumeLesson) {
    return null;
  }

  const completedSteps = Math.min(resumeLesson.completedBlocks, resumeLesson.totalBlocks);
  const remainingSteps = Math.max(resumeLesson.totalBlocks - completedSteps, 0);
  const progressPercent =
    resumeLesson.totalBlocks > 0 ? Math.round((completedSteps / resumeLesson.totalBlocks) * 100) : 0;
  const estimatedMinutesLeft = remainingSteps > 0 ? Math.max(3, Math.min(12, remainingSteps * 2)) : 0;
  const estimatedTimeText =
    estimatedMinutesLeft > 0
      ? estimatedMinutesLeft <= 4
        ? tr("About 3-4 minutes")
        : estimatedMinutesLeft <= 8
          ? tr("About 5-8 minutes")
          : tr("About 10-12 minutes")
      : tr("Almost done");
  const progressState =
    progressPercent < 30
      ? tr("The base of the lesson is forming now")
      : progressPercent <= 70
        ? tr("You are already in the lesson; only a little is left")
        : tr("Final stage; now we secure the result");

  return (
    <Card className="space-y-5 border border-white/70 bg-white/78 shadow-soft">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="inline-flex rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
            {tr("Lesson is open")}
          </div>
          <div className="mt-4 max-w-3xl text-3xl font-semibold leading-tight text-ink">
            {tr(resumeLesson.title)}
          </div>
          <div className="mt-3 text-sm text-slate-600">
            {tr("You are here")}: <span className="font-semibold text-ink">{tr(resumeLesson.currentBlockTitle)}</span>
          </div>
        </div>
        <div className="rounded-[22px] bg-sand/70 px-4 py-3 text-sm font-semibold text-ink">
          {estimatedTimeText}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[26px] bg-white/82 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="font-semibold text-ink">{tr("You are moving")}</div>
            <div className="text-slate-600">{progressPercent}%</div>
          </div>
          <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200/70">
            <div
              className="h-full rounded-full bg-accent transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="mt-3 rounded-2xl bg-accent/8 px-3 py-2 text-sm font-semibold text-accent">
            {progressState}
          </div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {tr("A few steps left")}
          </div>
          <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
            <div className="rounded-2xl bg-mint/30 p-3">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{tr("Already done")}</div>
              <div className="mt-1 font-semibold text-ink">
                {completedSteps} {tr(completedSteps === 1 ? "step" : "steps")}
              </div>
            </div>
            <div className="rounded-2xl bg-mint/30 p-3">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{tr("Still ahead")}</div>
              <div className="mt-1 font-semibold text-ink">
                {remainingSteps} {tr(remainingSteps === 1 ? "short step" : "short steps")}
              </div>
            </div>
            <div className="rounded-2xl bg-mint/30 p-3">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{tr("About time")}</div>
              <div className="mt-1 font-semibold text-ink">
                {estimatedTimeText}
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-[26px] border border-accent/18 bg-accent/8 p-4 text-sm leading-6 text-slate-700">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{tr("Why now")}</div>
          <div className="mt-3">
            {tr("Finish now, and you will not lose the thread. Then I will show the next step.")}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        {showPrimaryAction ? (
          <Button onClick={onResumeLesson} className="px-6 py-3 text-base">
            {tr("Resume lesson")}
          </Button>
        ) : null}
        <Button
          variant="ghost"
          onClick={() => void onRestartLesson()}
          className="border border-slate-300/70 bg-white/44 text-slate-700 hover:bg-white/70"
        >
          {tr("Restart lesson")}
        </Button>
        <button
          type="button"
          onClick={() => void onDiscardLessonRun()}
          className="px-2 py-2 text-sm font-semibold text-slate-500 transition-colors hover:text-ink"
        >
          {tr("Close unfinished lesson")}
        </button>
      </div>
    </Card>
  );
}

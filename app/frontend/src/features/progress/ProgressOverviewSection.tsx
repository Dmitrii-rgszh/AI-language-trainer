import type { LessonHistoryItem, ProgressSnapshot } from "../../entities/progress/model";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";

type ProgressOverviewSectionProps = {
  averageLessonScore: number;
  dailyGoalProgress: number;
  formatDate: (value: string) => string;
  formatDays: (value: number) => string;
  mostRecentLesson: LessonHistoryItem | null;
  progress: ProgressSnapshot;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ProgressOverviewSection({
  averageLessonScore,
  dailyGoalProgress,
  formatDate,
  formatDays,
  mostRecentLesson,
  progress,
  tr,
  tt,
}: ProgressOverviewSectionProps) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ScoreBadge label={tr("Grammar")} score={progress.grammarScore} />
        <ScoreBadge label={tr("Speaking")} score={progress.speakingScore} />
        <ScoreBadge label={tr("Pronunciation")} score={progress.pronunciationScore} />
        <ScoreBadge label={tr("Writing")} score={progress.writingScore} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Daily goal")}</div>
          <div className="text-3xl font-semibold text-ink">
            {progress.minutesCompletedToday}/{progress.dailyGoalMinutes} min
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-sand">
            <div className="h-full rounded-full bg-accent" style={{ width: `${dailyGoalProgress}%` }} />
          </div>
          <div className="text-sm text-slate-600">{tr("Today completion")}: {dailyGoalProgress}%</div>
        </Card>

        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Consistency")}</div>
          <div className="text-3xl font-semibold text-ink">{formatDays(progress.streak)}</div>
          <div className="text-sm text-slate-600">{tr("Current streak across active learning days.")}</div>
        </Card>

        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">
            {tr("Average lesson score")}
          </div>
          <div className="text-3xl font-semibold text-ink">{averageLessonScore}</div>
          <div className="text-sm text-slate-600">
            {tr("Based on")} {progress.history.length}{" "}
            {tr(progress.history.length === 1 ? "completed lesson" : "completed lessons")}.
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Learning balance")}</div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Listening score")}: <span className="font-semibold text-ink">{progress.listeningScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Profession score")}: <span className="font-semibold text-ink">{progress.professionScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Regulation score")}: <span className="font-semibold text-ink">{progress.regulationScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent lessons")}: <span className="font-semibold text-ink">{progress.history.length}</span>
            </div>
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Recent highlight")}</div>
          {mostRecentLesson ? (
            <div className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(mostRecentLesson.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                    {tt(mostRecentLesson.lessonType)}
                  </div>
                </div>
                <div className="text-sm text-slate-600">
                  {tr("Score")} {mostRecentLesson.score}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">
                {tr("Last completed at")} {formatDate(mostRecentLesson.completedAt)}.
              </div>
            </div>
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("First completed lesson will appear here as soon as history starts filling up.")}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

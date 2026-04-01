import { Link } from "react-router-dom";
import type { LessonResultSummary } from "../../entities/lesson/model";
import type { ProgressSnapshot } from "../../entities/progress/model";
import type { PronunciationTrend } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Card } from "../../shared/ui/Card";

type ActivityOverviewSectionProps = {
  lastLessonResult: LessonResultSummary | null;
  mistakesCount: number;
  progress: ProgressSnapshot;
  pronunciationTrend: PronunciationTrend | null;
  speakingAttemptsCount: number;
  tr: (value: string) => string;
};

export function ActivityOverviewSection({
  lastLessonResult,
  mistakesCount,
  progress,
  pronunciationTrend,
  speakingAttemptsCount,
  tr,
}: ActivityOverviewSectionProps) {
  return (
    <>
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Lessons")}</div>
          <div className="text-3xl font-semibold text-ink">{progress.history.length}</div>
          <div className="text-sm text-slate-600">{tr("Completed lessons in current progress history.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Speaking attempts")}</div>
          <div className="text-3xl font-semibold text-ink">{speakingAttemptsCount}</div>
          <div className="text-sm text-slate-600">{tr("Voice and text practice attempts collected so far.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Open patterns")}</div>
          <div className="text-3xl font-semibold text-ink">{mistakesCount}</div>
          <div className="text-sm text-slate-600">{tr("Mistake records currently tracked in the system.")}</div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Latest result")}</div>
          <div className="text-3xl font-semibold text-ink">{lastLessonResult?.score ?? "-"}</div>
          <div className="text-sm text-slate-600">
            {lastLessonResult ? tr("Current session lesson result is available.") : tr("No current session result yet.")}
          </div>
        </Card>
      </div>

      {pronunciationTrend ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Pronunciation contribution")}</div>
            <Link to={routes.pronunciation} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open lab")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Average score")}: <span className="font-semibold text-ink">{pronunciationTrend.averageScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent checks")}: <span className="font-semibold text-ink">{pronunciationTrend.recentAttempts}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Top weak sound")}:{" "}
              <span className="font-semibold text-ink">{pronunciationTrend.weakestSounds[0]?.label ?? tr("stable")}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {pronunciationTrend.weakestSounds.length > 0
              ? `${tr("This area is now part of the overall learning signal")}: ${pronunciationTrend.weakestSounds
                  .map((item) => `${item.label} (${item.occurrences}x)`)
                  .join(", ")}.`
              : tr("Pronunciation looks stable enough that no repeating weak sound is dominating activity yet.")}
          </div>
        </Card>
      ) : null}
    </>
  );
}

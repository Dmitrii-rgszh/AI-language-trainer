import type { ProgressSnapshot } from "../../entities/progress/model";
import type { SpeakingAttempt } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type ProgressHistorySectionProps = {
  activityError: string | null;
  feedbackSourceLabel: (source: SpeakingAttempt["feedbackSource"]) => string;
  formatDate: (value: string) => string;
  formatDateTime: (value: string) => string;
  progress: ProgressSnapshot;
  recentSpeakingAttempts: SpeakingAttempt[];
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ProgressHistorySection({
  activityError,
  feedbackSourceLabel,
  formatDate,
  formatDateTime,
  progress,
  recentSpeakingAttempts,
  tr,
  tt,
}: ProgressHistorySectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Lesson history")}</div>
        {progress.history.map((item) => (
          <div key={item.id} className="rounded-2xl bg-white/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-ink">{tr(item.title)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.lessonType)}</div>
              </div>
              <div className="text-sm text-slate-600">
                {formatDate(item.completedAt)} • {tr("score")} {item.score}
              </div>
            </div>
          </div>
        ))}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Speaking activity")}</div>
        {activityError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {activityError}
          </div>
        ) : null}
        {recentSpeakingAttempts.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Voice and text speaking attempts will appear here after the first practice session.")}
          </div>
        ) : (
          recentSpeakingAttempts.map((attempt) => (
            <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(attempt.scenarioTitle)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                    {tt(attempt.inputMode)} • {feedbackSourceLabel(attempt.feedbackSource)}
                  </div>
                </div>
                <div className="text-sm text-slate-600">{formatDateTime(attempt.createdAt)}</div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{attempt.feedbackSummary}</div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

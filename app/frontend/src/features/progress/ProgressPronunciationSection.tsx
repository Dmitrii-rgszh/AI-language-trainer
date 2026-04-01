import type { ProgressSnapshot } from "../../entities/progress/model";
import type { PronunciationTrend } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type ProgressPronunciationSectionProps = {
  progress: ProgressSnapshot;
  pronunciationTrend: PronunciationTrend | null;
  tr: (value: string) => string;
};

export function ProgressPronunciationSection({
  progress,
  pronunciationTrend,
  tr,
}: ProgressPronunciationSectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Pronunciation contribution")}</div>
        {pronunciationTrend ? (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Average score")}: <span className="font-semibold text-ink">{pronunciationTrend.averageScore}</span>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Recent checks")}: <span className="font-semibold text-ink">{pronunciationTrend.recentAttempts}</span>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Pronunciation")} score: <span className="font-semibold text-ink">{progress.pronunciationScore}</span>
              </div>
            </div>
            <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
              {pronunciationTrend.weakestSounds.length > 0
                ? `${tr("Recurring weak sounds")}: ${pronunciationTrend.weakestSounds
                    .map((item) => `${item.label} (${item.occurrences}x)`)
                    .join(", ")}.`
                : tr("No repeating weak sound pattern detected yet.")}
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {pronunciationTrend.weakestWords.length > 0
                ? `${tr("Recurring weak words")}: ${pronunciationTrend.weakestWords
                    .map((item) => `${item.label} (${item.occurrences}x)`)
                    .join(", ")}.`
                : tr("Weak-word trend will appear after repeated pronunciation checks.")}
            </div>
          </>
        ) : (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Pronunciation trend data will appear here after the first saved audio checks.")}
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Roadmap reading")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Pronunciation now contributes through saved audio checks, not just a single lab verdict.")}
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr(
            "If repeating weak sounds stay visible here, your readiness to the next milestone should be treated as less stable even when grammar or writing move faster.",
          )}
        </div>
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {tr(
            "Use `Pronunciation Lab` to clear the top weak sound, then rerun a checkpoint to see whether the roadmap shifts upward more confidently.",
          )}
        </div>
      </Card>
    </div>
  );
}

import type { AdaptiveStudyLoop, ListeningAttempt, ListeningTrend } from "../../shared/types/app-data";
import { resolutionTone } from "../../shared/activity/resolution-tone";
import { Card } from "../../shared/ui/Card";

type ProgressSignalsSectionProps = {
  formatDays: (value: number) => string;
  listeningAttempts: ListeningAttempt[];
  listeningTrend: ListeningTrend | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ProgressSignalsSection({
  formatDays,
  listeningAttempts,
  listeningTrend,
  studyLoop,
  tr,
  tt,
}: ProgressSignalsSectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Mistake to vocabulary contribution")}</div>
        {studyLoop?.vocabularyBacklinks.length ? (
          <>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr(
                "Some weak spots are already being recycled into vocabulary review, so the app is no longer treating them as isolated corrections.",
              )}
            </div>
            {studyLoop.vocabularyBacklinks.map((link) => (
              <div key={link.weakSpotTitle} className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                <div className="font-semibold text-ink">{tr(link.weakSpotTitle)}</div>
                <div className="mt-2">
                  {link.dueCount} {tr("due")} and {link.activeCount} {tr("active")} vocabulary items now reinforce
                  this weak spot.
                </div>
                <div className="mt-2">Examples: {link.exampleWords.join(", ")}.</div>
                <div className="mt-2 text-xs uppercase tracking-[0.12em] text-slate-500">
                  {tr("sources")}: {link.sourceModules.map((item) => tt(item)).join(", ")}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Once weak spots start converting into vocabulary review, the closed loop will appear here.")}
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Recovering weak spots")}</div>
        {studyLoop?.mistakeResolution.length ? (
          studyLoop.mistakeResolution.map((item) => (
            <div key={item.weakSpotTitle} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-semibold text-ink">{tr(item.weakSpotTitle)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.weakSpotCategory)}</div>
                </div>
                <div
                  className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${resolutionTone(item.status)}`}
                >
                  {tr(item.status)}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">
                {tr("Repeats")} {item.repetitionCount}. {tr("Last seen")} {formatDays(item.lastSeenDaysAgo)} ago.
              </div>
              <div className="mt-2 text-sm text-slate-600">
                {tr("Linked vocabulary support")}: {item.linkedVocabularyCount}.
              </div>
              <div className="mt-3 rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">{tr(item.resolutionHint)}</div>
            </div>
          ))
        ) : (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr(
              "Recovery visibility will appear once weak spots have enough history to show whether they are staying active or starting to settle down.",
            )}
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Listening activity")}</div>
        {listeningTrend ? (
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Average score")} {listeningTrend.averageScore}. Transcript support used in{" "}
            {listeningTrend.transcriptSupportRate}% of recent attempts.
          </div>
        ) : null}
        {listeningAttempts.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Listening attempts will appear here after completing audio-first lesson blocks.")}
          </div>
        ) : (
          listeningAttempts.slice(0, 4).map((attempt) => (
            <div key={attempt.id} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(attempt.lessonTitle)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                    {attempt.promptLabel ? tr(attempt.promptLabel) : tr(attempt.blockTitle)}
                  </div>
                </div>
                <div className="text-sm text-slate-600">
                  {tr("score")} {attempt.score}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{attempt.answerSummary}</div>
              <div className="mt-2 text-xs text-slate-500">
                {attempt.usedTranscriptSupport ? tr("Transcript support used") : tr("Audio-first answer")}
              </div>
            </div>
          ))
        )}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Listening trend reading")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Listening now has saved attempt memory, not just one score inside the roadmap.")}
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {listeningTrend?.weakestPrompts.length
            ? `${tr("Recurring weak prompts")}: ${listeningTrend.weakestPrompts
                .map((item) => `${item.label} (${item.occurrences}x)`)
                .join(", ")}.`
            : tr("No recurring weak listening prompt has emerged yet.")}
        </div>
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {tr("Use transcript support rate as a confidence signal: lower support over time means listening is stabilizing.")}
        </div>
      </Card>
    </div>
  );
}

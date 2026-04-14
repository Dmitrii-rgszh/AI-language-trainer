import type { JourneySessionSummary } from "../../shared/types/app-data";

type JourneySessionSummaryPanelProps = {
  summary: JourneySessionSummary;
  title: string;
  tr: (value: string) => string;
};

function formatOutcomeLabel(outcomeBand: string, tr: (value: string) => string) {
  switch (outcomeBand) {
    case "breakthrough":
      return tr("Breakthrough");
    case "stable":
      return tr("Stable signal");
    case "fragile":
      return tr("Needs protection");
    case "checkpoint":
      return tr("Checkpoint signal");
    default:
      return tr("Session signal");
  }
}

function formatLeadOutcomeLabel(outcome: string | null | undefined, tr: (value: string) => string) {
  switch (outcome) {
    case "held":
      return tr("Held well");
    case "usable":
      return tr("Usable signal");
    case "fragile":
      return tr("Still fragile");
    case "unmeasured":
      return tr("Not measured");
    default:
      return tr("Route signal");
  }
}

export function JourneySessionSummaryPanel({
  summary,
  title,
  tr,
}: JourneySessionSummaryPanelProps) {
  const practiceShift = summary.practiceMixEvaluation ?? null;
  const signalPills = [
    summary.carryOverSignalLabel
      ? `${tr("Carry forward")}: ${summary.carryOverSignalLabel}`
      : null,
    summary.watchSignalLabel
      ? `${tr("Watch next")}: ${summary.watchSignalLabel}`
      : null,
    summary.weakSpotTitle
      ? `${tr("Weak spot")}: ${summary.weakSpotTitle}`
      : null,
  ].filter((item): item is string => Boolean(item));

  return (
    <div className="rounded-[24px] border border-white/70 bg-white/80 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.18em] text-coral">{title}</div>
        <div className="rounded-full bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
          {formatOutcomeLabel(summary.outcomeBand, tr)}
        </div>
      </div>

      <div className="mt-3 text-lg font-semibold text-ink">{summary.headline}</div>

      {signalPills.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {signalPills.map((pill) => (
            <div
              key={pill}
              className="rounded-full border border-white/70 bg-sand/70 px-3 py-1 text-xs font-semibold text-slate-700"
            >
              {pill}
            </div>
          ))}
        </div>
      ) : null}

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-[20px] bg-sand/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("What worked")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{summary.whatWorked}</div>
        </div>
        <div className="rounded-[20px] bg-white/86 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("What still needs watch")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{summary.watchSignal}</div>
        </div>
      </div>

      <div className="mt-3 rounded-[20px] border border-accent/15 bg-accent/8 p-4 text-sm leading-6 text-slate-700">
        <span className="font-semibold text-ink">{tr("Strategy shift")}:</span> {summary.strategyShift}
      </div>

      {practiceShift ? (
        <div className="mt-3 rounded-[20px] border border-coral/15 bg-coral/6 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-xs uppercase tracking-[0.16em] text-coral">{tr("Practice shift")}</div>
            <div className="rounded-full bg-white/86 px-3 py-1 text-xs font-semibold text-coral">
              {formatLeadOutcomeLabel(practiceShift.leadOutcome, tr)}
            </div>
          </div>

          <div className="mt-3 text-sm leading-6 text-slate-700">
            {practiceShift.summaryLine ?? tr("The system is now tracking which practice type held the route and which one still needs support.")}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-[18px] bg-white/82 p-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Lead practice")}</div>
              <div className="mt-2 font-semibold text-ink">{practiceShift.leadPracticeTitle ?? tr("Route signal")}</div>
              {typeof practiceShift.leadAverageScore === "number" ? (
                <div className="mt-1 text-xs text-slate-500">{practiceShift.leadAverageScore}/100</div>
              ) : null}
            </div>
            <div className="rounded-[18px] bg-white/82 p-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Strongest practice")}</div>
              <div className="mt-2 font-semibold text-ink">{practiceShift.strongestPracticeTitle ?? tr("Route signal")}</div>
              {typeof practiceShift.strongestPracticeScore === "number" ? (
                <div className="mt-1 text-xs text-slate-500">{practiceShift.strongestPracticeScore}/100</div>
              ) : null}
            </div>
            <div className="rounded-[18px] bg-white/82 p-3 text-sm text-slate-700">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Needs support")}</div>
              <div className="mt-2 font-semibold text-ink">{practiceShift.weakestPracticeTitle ?? tr("Weak signal")}</div>
              {typeof practiceShift.weakestPracticeScore === "number" ? (
                <div className="mt-1 text-xs text-slate-500">{practiceShift.weakestPracticeScore}/100</div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-3 text-sm leading-6 text-slate-600">{summary.coachNote}</div>
    </div>
  );
}

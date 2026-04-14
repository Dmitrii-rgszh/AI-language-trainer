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

export function JourneySessionSummaryPanel({
  summary,
  title,
  tr,
}: JourneySessionSummaryPanelProps) {
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

      <div className="mt-3 text-sm leading-6 text-slate-600">{summary.coachNote}</div>
    </div>
  );
}

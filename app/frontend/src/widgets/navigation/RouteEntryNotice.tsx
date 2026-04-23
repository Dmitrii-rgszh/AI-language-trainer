import { Button } from "../../shared/ui/Button";

type RouteEntryNoticeProps = {
  reason: string;
  currentLabel?: string | null;
  followUpLabel?: string | null;
  carryLabel?: string | null;
  stageLabel?: string | null;
  sourceLabel?: string | null;
  onDismiss: () => void;
  tr: (value: string) => string;
};

export function RouteEntryNotice({
  reason,
  currentLabel,
  followUpLabel,
  carryLabel,
  stageLabel,
  sourceLabel,
  onDismiss,
  tr,
}: RouteEntryNoticeProps) {
  const hasDistinctFollowUp = followUpLabel && followUpLabel !== currentLabel;
  const hasDistinctCarry =
    carryLabel && carryLabel !== currentLabel && carryLabel !== followUpLabel;

  return (
    <div className="mt-4 rounded-[24px] border border-accent/10 bg-white/40 p-3 shadow-none backdrop-blur">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="text-[0.68rem] uppercase tracking-[0.22em] text-coral">{tr("Continue lesson")}</div>
          <div className="mt-1 text-lg font-[700] tracking-[-0.02em] text-ink">{tr("Continue from here")}</div>
          <div className="mt-1 text-sm leading-6 text-slate-600">
            {currentLabel ? (
              <>
                {tr("Now")}: <span className="font-semibold text-ink">{tr(currentLabel)}</span>
              </>
            ) : (
              tr("Now: warm-up before speaking")
            )}
          </div>

          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-[700] text-slate-500 transition-colors hover:text-ink">
              {tr("How this lesson is built")}
            </summary>
            <div className="mt-3 rounded-[22px] bg-white/72 p-3 text-sm leading-6 text-slate-600">
              <div>{reason}</div>
              {currentLabel || hasDistinctFollowUp || hasDistinctCarry ? (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {currentLabel ? (
                    <span className="rounded-full bg-accent/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-accent">
                      {tr("Now")}: {tr(currentLabel)}
                    </span>
                  ) : null}
                  {hasDistinctFollowUp ? (
                    <span className="rounded-full bg-coral/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-coral">
                      {tr("Then")}: {tr(followUpLabel ?? "")}
                    </span>
                  ) : null}
                  {hasDistinctCarry ? (
                    <span className="rounded-full bg-sand px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-ink">
                      {tr("Carry")}: {tr(carryLabel ?? "")}
                    </span>
                  ) : null}
                </div>
              ) : null}
              {stageLabel || sourceLabel ? (
                <div className="mt-3 flex flex-wrap gap-2 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-slate-500">
                  {stageLabel ? <span className="rounded-full bg-white/82 px-3 py-1">{tr(stageLabel)}</span> : null}
                  {sourceLabel ? <span className="rounded-full bg-white/82 px-3 py-1">{sourceLabel}</span> : null}
                </div>
              ) : null}
            </div>
          </details>
        </div>

        <div className="flex shrink-0 flex-wrap gap-3">
          <Button type="button" variant="ghost" onClick={onDismiss}>
            {tr("Hide")}
          </Button>
        </div>
      </div>
    </div>
  );
}

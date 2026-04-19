import { Button } from "../../shared/ui/Button";

type RouteEntryNoticeProps = {
  reason: string;
  currentLabel?: string | null;
  followUpLabel?: string | null;
  stageLabel?: string | null;
  sourceLabel?: string | null;
  onDismiss: () => void;
  tr: (value: string) => string;
};

export function RouteEntryNotice({
  reason,
  currentLabel,
  followUpLabel,
  stageLabel,
  sourceLabel,
  onDismiss,
  tr,
}: RouteEntryNoticeProps) {
  return (
    <div className="mt-4 rounded-[28px] border border-accent/15 bg-accent/6 p-4 shadow-soft backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="text-[0.68rem] uppercase tracking-[0.22em] text-coral">{tr("Route entry")}</div>
          <div className="mt-2 text-lg font-[700] tracking-[-0.02em] text-ink">{tr("Liza moved you into the stronger starting point")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{reason}</div>
          {currentLabel || followUpLabel ? (
            <div className="mt-3 rounded-[22px] bg-white/82 p-3 text-sm text-slate-700">
              <div className="text-[0.68rem] font-[700] uppercase tracking-[0.14em] text-slate-500">
                {tr("Route flow")}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {currentLabel ? (
                  <span className="rounded-full bg-accent/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-accent">
                    {tr("Now")}: {currentLabel}
                  </span>
                ) : null}
                {followUpLabel ? (
                  <span className="rounded-full bg-coral/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-coral">
                    {tr("Then")}: {followUpLabel}
                  </span>
                ) : null}
              </div>
            </div>
          ) : null}
          {stageLabel ? (
            <div className="mt-3 flex flex-wrap gap-2 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-slate-500">
              {stageLabel ? (
                <span className="rounded-full bg-white/82 px-3 py-1">
                  {stageLabel}
                </span>
              ) : null}
            </div>
          ) : null}
          {sourceLabel ? (
            <div className="mt-3 inline-flex rounded-full bg-white/82 px-3 py-1 text-[0.68rem] font-[700] uppercase tracking-[0.14em] text-slate-500">
              {sourceLabel}
            </div>
          ) : null}
        </div>

        <div className="flex shrink-0 flex-wrap gap-3">
          <Button type="button" variant="ghost" onClick={onDismiss}>
            {tr("Hide explanation")}
          </Button>
        </div>
      </div>
    </div>
  );
}

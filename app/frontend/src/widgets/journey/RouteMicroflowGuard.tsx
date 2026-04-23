type RouteMicroflowGuardProps = {
  label?: string;
  message: string;
  ritualWindowTitle?: string | null;
  ritualWindowSummary?: string | null;
  dayShapeTitle?: string | null;
  dayShapeCompactnessLabel?: string | null;
  dayShapeSummary?: string | null;
  dayShapeExpansionStageLabel?: string | null;
  dayShapeExpansionWindowLabel?: string | null;
  tr: (value: string) => string;
};

export function RouteMicroflowGuard({
  label,
  message,
  ritualWindowTitle,
  ritualWindowSummary,
  dayShapeTitle,
  dayShapeCompactnessLabel,
  dayShapeSummary,
  dayShapeExpansionStageLabel,
  dayShapeExpansionWindowLabel,
  tr,
}: RouteMicroflowGuardProps) {
  return (
    <div className="space-y-3 rounded-2xl border border-dashed border-slate-300/90 bg-white/70 p-4 text-sm leading-6 text-slate-600">
      <div>
        <span className="font-semibold text-ink">{label ?? tr("Protected route guard")}: </span>
        {message}
      </div>

      {dayShapeTitle ? (
        <div className="rounded-2xl bg-sand/70 p-3">
          <div className="text-[0.68rem] uppercase tracking-[0.18em] text-slate-400">{tr("Day shape")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {dayShapeTitle}
            {dayShapeCompactnessLabel ? ` · ${dayShapeCompactnessLabel}` : ""}
          </div>
          {dayShapeExpansionStageLabel ? (
            <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent">
              {dayShapeExpansionStageLabel}
            </div>
          ) : null}
          {dayShapeExpansionWindowLabel ? (
            <div className="mt-2 text-xs text-slate-500">{dayShapeExpansionWindowLabel}</div>
          ) : null}
          {dayShapeSummary ? (
            <div className="mt-2 text-sm text-slate-600">{dayShapeSummary}</div>
          ) : null}
        </div>
      ) : null}

      {ritualWindowTitle ? (
        <div className="rounded-2xl bg-white/82 p-3">
          <div className="text-[0.68rem] uppercase tracking-[0.18em] text-slate-400">{tr("Ritual arc")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">{ritualWindowTitle}</div>
          {ritualWindowSummary ? (
            <div className="mt-2 text-sm text-slate-600">{ritualWindowSummary}</div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

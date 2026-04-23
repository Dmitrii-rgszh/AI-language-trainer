import { Link } from "react-router-dom";
import type { ScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import { Card } from "../../shared/ui/Card";

type RouteGovernanceNoticeProps = {
  governance: ScreenRouteGovernanceView;
  tr: (value: string) => string;
};

export function RouteGovernanceNotice({ governance, tr }: RouteGovernanceNoticeProps) {
  if (governance.state === "open") {
    return null;
  }

  return (
    <Card className="space-y-4 border border-accent/15 bg-accent/5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.2em] text-coral">{tr("Route governance")}</div>
          <div className="mt-2 text-xl font-semibold text-ink">{governance.title}</div>
        </div>
        <div className="rounded-full bg-white/85 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-600">
          {governance.badgeLabel}
        </div>
      </div>

      <div className="rounded-[20px] bg-white/80 p-4 text-sm leading-6 text-slate-700">
        {governance.summary}
      </div>

      {governance.dayShapeTitle ? (
        <div className={`grid gap-3 ${governance.dayShapeSequenceLabel ? "md:grid-cols-2" : ""}`}>
          <div className="rounded-[20px] bg-sand/70 p-4">
            <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Day shape")}</div>
            <div className="mt-2 text-sm font-semibold text-ink">
              {governance.dayShapeTitle}
              {governance.dayShapeCompactnessLabel ? ` · ${governance.dayShapeCompactnessLabel}` : ""}
            </div>
            {governance.dayShapeExpansionStageLabel ? (
              <div className="mt-2 text-xs font-semibold uppercase tracking-[0.16em] text-accent">
                {governance.dayShapeExpansionStageLabel}
              </div>
            ) : null}
            {governance.dayShapeExpansionWindowLabel ? (
              <div className="mt-2 text-xs text-slate-500">{governance.dayShapeExpansionWindowLabel}</div>
            ) : null}
            <div className="mt-2 text-sm text-slate-600">
              {governance.dayShapeSummary}
            </div>
          </div>

          {governance.dayShapeSequenceLabel ? (
            <div className="rounded-[20px] bg-white/82 p-4">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Re-entry step")}</div>
              <div className="mt-2 text-sm font-semibold text-ink">{governance.dayShapeSequenceLabel}</div>
              <div className="mt-2 text-sm text-slate-600">
                {tr("This support surface is being reopened in the sequence chosen for today's route rhythm.")}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      {governance.ritualWindowTitle ? (
        <div className="rounded-[20px] bg-white/82 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Ritual arc")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">{governance.ritualWindowTitle}</div>
          {governance.ritualWindowSummary ? (
            <div className="mt-2 text-sm text-slate-600">{governance.ritualWindowSummary}</div>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Link to={governance.primaryRoute} className="proof-lesson-primary-button">
          {governance.primaryLabel}
        </Link>
        <Link to={governance.secondaryRoute} className="proof-lesson-secondary-action">
          {governance.secondaryLabel}
        </Link>
      </div>
    </Card>
  );
}

import { Link } from "react-router-dom";
import type { WeakSpot } from "../../entities/mistake/model";
import type { QuickAction } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type DashboardWeakSpotsAndActionsSectionProps = {
  quickActions: QuickAction[];
  tr: (value: string) => string;
  tt: (value: string) => string;
  weakSpots: WeakSpot[];
};

export function DashboardWeakSpotsAndActionsSection({
  quickActions,
  tr,
  tt,
  weakSpots,
}: DashboardWeakSpotsAndActionsSectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Weak spots")}</div>
          <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
            {weakSpots.length} {tr("active")}
          </div>
        </div>
        {weakSpots.map((spot) => (
          <div key={spot.id} className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr(spot.title)}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(spot.category)}</div>
            <div className="mt-2 text-sm text-slate-600">{tr(spot.recommendation)}</div>
          </div>
        ))}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Next route actions")}</div>
        {quickActions.map((action, index) => (
          action.disabled ? (
            <div
              key={action.id}
              className="block rounded-2xl border border-dashed border-slate-300/90 bg-white/55 p-4 text-slate-400"
              aria-disabled="true"
            >
              <div className="text-sm font-semibold text-slate-500">{tr(action.title)}</div>
              {index === 0 ? (
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tr("Main path")}</div>
              ) : (
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {tr("Later in today’s route")}
                </div>
              )}
              <div className="mt-2 text-sm text-slate-500">{tr(action.description)}</div>
              {action.disabledReason ? (
                <div className="mt-3 rounded-2xl bg-white/85 px-3 py-2 text-xs leading-5 text-slate-500">
                  {tr(action.disabledReason)}
                </div>
              ) : null}
            </div>
          ) : (
            <Link
              key={action.id}
              to={action.route}
              className={`block rounded-2xl p-4 ${
                action.tone === "primary"
                  ? "border border-accent/20 bg-accent/8"
                  : action.tone === "support"
                    ? "bg-sand/70"
                    : "bg-white/70"
              }`}
            >
              <div className="text-sm font-semibold text-ink">{tr(action.title)}</div>
              {index === 0 ? (
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tr("Main path")}</div>
              ) : action.tone === "support" ? (
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{tr("Supports today’s rhythm")}</div>
              ) : null}
              <div className="mt-2 text-sm text-slate-600">{tr(action.description)}</div>
            </Link>
          )
        ))}
      </Card>
    </div>
  );
}

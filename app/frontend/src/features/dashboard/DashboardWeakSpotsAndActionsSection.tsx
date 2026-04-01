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
        <div className="text-lg font-semibold text-ink">{tr("Quick actions")}</div>
        {quickActions.map((action) => (
          <Link key={action.id} to={action.route} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr(action.title)}</div>
            <div className="mt-2 text-sm text-slate-600">{tr(action.description)}</div>
          </Link>
        ))}
      </Card>
    </div>
  );
}

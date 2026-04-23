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
  quickActions: _quickActions,
  tr,
  tt,
  weakSpots,
}: DashboardWeakSpotsAndActionsSectionProps) {
  const visibleWeakSpots = weakSpots.slice(0, 2);
  const describeWeakSpot = (spot: WeakSpot) => {
    if (spot.category === "profession") {
      return tr("We will try saying it out loud.");
    }
    if (spot.category === "pronunciation") {
      return tr("We will say it slowly and clearly.");
    }
    return tr("We will repeat it briefly.");
  };

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3 bg-white/68 shadow-none">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("What is next")}</div>
          <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
            {visibleWeakSpots.length} {tr("topics")}
          </div>
        </div>
        {visibleWeakSpots.map((spot) => (
          <div key={spot.id} className="rounded-2xl bg-white/58 p-4">
            <div className="text-sm font-semibold text-ink">{tr(spot.title)}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(spot.category)}</div>
            <div className="mt-2 text-sm text-slate-600">→ {describeWeakSpot(spot)}</div>
          </div>
        ))}
      </Card>

      <Card className="space-y-2 border-white/25 bg-white/24 p-4 shadow-none">
        <div>
          <div className="text-sm font-semibold text-slate-500">{tr("You can look here later")}</div>
          <div className="mt-1 text-xs text-slate-400">{tr("Better finish the lesson first")}</div>
        </div>
      </Card>
    </div>
  );
}

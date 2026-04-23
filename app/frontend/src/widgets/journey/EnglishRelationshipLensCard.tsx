import type { EnglishRelationshipLens } from "../../shared/journey/english-relationship-lens";
import { Card } from "../../shared/ui/Card";

type EnglishRelationshipLensCardProps = {
  lens: EnglishRelationshipLens;
  tr: (value: string) => string;
};

export function EnglishRelationshipLensCard({
  lens,
  tr,
}: EnglishRelationshipLensCardProps) {
  return (
    <Card className="space-y-4 border border-accent/20 bg-accent/6">
      <div className="text-xs font-semibold uppercase tracking-[0.22em] text-coral">
        {tr("You & English lens")}
      </div>
      <div className="text-lg font-semibold text-ink">{lens.title}</div>
      <div className="rounded-[20px] bg-white/82 p-4 text-sm leading-6 text-slate-700">
        {lens.principle}
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-[18px] bg-white/82 p-4 text-sm text-slate-700">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            {lens.successLabel}
          </div>
          <div className="mt-2 leading-6">{lens.successSummary}</div>
        </div>
        <div className="rounded-[18px] bg-sand/75 p-4 text-sm text-slate-700">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            {tr("Pressure release")}
          </div>
          <div className="mt-2 leading-6">{lens.pressureRelease}</div>
        </div>
      </div>
    </Card>
  );
}

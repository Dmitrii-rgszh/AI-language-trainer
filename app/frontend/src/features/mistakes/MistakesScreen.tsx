import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { buildScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { RouteGovernanceNotice } from "../../widgets/journey/RouteGovernanceNotice";

export function MistakesScreen() {
  const { tr, tt } = useLocale();
  const dashboard = useAppStore((state) => state.dashboard);
  const mistakes = useAppStore((state) => state.mistakes);
  const routeGovernance = buildScreenRouteGovernanceView(dashboard ?? null, routes.mistakes, tr);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Mistake Analytics")}
        title={tr("My Mistakes")}
        description={tr("Review recurring patterns, compare corrections, and see what still needs active recovery.")}
      />

      <RouteGovernanceNotice governance={routeGovernance} tr={tr} />

      {routeGovernance.isDeferred ? (
        <Card className="space-y-4 border border-accent/10 bg-white/75">
          <div className="text-sm leading-6 text-slate-700">
            {tr("The mistake map remains visible, but right now it should support today's protected return instead of pulling you into a separate repair branch too early.")}
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to={routeGovernance.primaryRoute} className="proof-lesson-primary-button">
              {routeGovernance.primaryLabel}
            </Link>
            <Link to={routeGovernance.secondaryRoute} className="proof-lesson-secondary-action">
              {routeGovernance.secondaryLabel}
            </Link>
          </div>
        </Card>
      ) : null}

      <div className="space-y-4">
        {mistakes.map((mistake) => (
          <Card key={mistake.id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{tr(mistake.subtype)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(mistake.category)}</div>
              </div>
              <div className="rounded-2xl bg-white/70 px-3 py-2 text-sm text-slate-700">
                {tr("repeats")}: {mistake.repetitionCount}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-[#fff0ea] p-4 text-sm text-slate-700">{mistake.originalText}</div>
              <div className="rounded-2xl bg-[#ecfffb] p-4 text-sm text-slate-700">{mistake.correctedText}</div>
            </div>

            <div className="text-sm leading-6 text-slate-700">{tr(mistake.explanation)}</div>
          </Card>
        ))}
      </div>
    </div>
  );
}

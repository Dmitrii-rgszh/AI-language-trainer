import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { resolveRouteFollowUpTransition } from "../../shared/journey/route-follow-up-navigation";
import { buildScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { RouteGovernanceNotice } from "../../widgets/journey/RouteGovernanceNotice";

export function ProfessionScreen() {
  const { tr, tt, tl } = useLocale();
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const tracks = useAppStore((state) => state.professionTracks);
  const navigate = useNavigate();
  const routeGovernance = buildScreenRouteGovernanceView(dashboard ?? null, routes.profession, tr);

  async function handleCompleteSupportStep() {
    const updatedState = await apiClient.completeRouteReentrySupportStep({ route: routes.profession });
    await bootstrap();
    const transition = resolveRouteFollowUpTransition(updatedState, routes.profession, tr);
    if (transition) {
      navigate(transition.route, {
        state: {
          routeEntryReason: transition.reason,
          routeEntrySource: "support_step_follow_up",
          routeEntryFollowUpLabel: transition.nextLabel ?? null,
          routeEntryStageLabel: transition.stageLabel ?? null,
        },
      });
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Professional English")}
        title={tr("Profession Hub")}
        description={tr("Choose the professional track that should shape your vocabulary, scenarios, and lesson emphasis.")}
      />

      <RouteGovernanceNotice governance={routeGovernance} tr={tr} />

      {routeGovernance.isPriorityReentry ? (
        <Card className="space-y-4 border border-accent/10 bg-white/75">
          <div className="text-sm leading-6 text-slate-700">
            {tr("This professional support surface is the right next re-entry step. When you have reviewed it, release the route so the next support module can reopen in sequence.")}
          </div>
          <div className="flex flex-wrap gap-3">
            <Button type="button" onClick={() => void handleCompleteSupportStep()} className="proof-lesson-primary-button">
              {tr("Finish profession support step")}
            </Button>
            <Link to={routeGovernance.primaryRoute} className="proof-lesson-secondary-action">
              {routeGovernance.primaryLabel}
            </Link>
          </div>
        </Card>
      ) : null}

      {routeGovernance.isDeferred ? (
        <Card className="space-y-4 border border-accent/10 bg-white/75">
          <div className="text-sm leading-6 text-slate-700">
            {tr("Professional English still matters here, but the system wants today's protected route to stay narrow before it widens back into domain-specific work.")}
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

      <div className="grid gap-4 lg:grid-cols-2">
        {tracks.map((track) => (
          <Card key={track.id} className="space-y-4">
            <div>
              <div className="text-lg font-semibold text-ink">{tr(track.title)}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(track.domain)}</div>
            </div>
            <div className="text-sm leading-6 text-slate-700">{tr(track.summary)}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {track.lessonFocus.map((focus) => (
                <div key={focus}>• {tl([focus])}</div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

import type { LearnerJourneyState } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type LearningBlueprintPanelProps = {
  journeyState: LearnerJourneyState | null;
  tr: (value: string) => string;
};

export function LearningBlueprintPanel({ journeyState, tr }: LearningBlueprintPanelProps) {
  const blueprint = journeyState?.strategySnapshot.learningBlueprint ?? null;

  if (!blueprint) {
    return null;
  }

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">
            {tr("Learning blueprint")}
          </div>
          <div className="mt-2 text-2xl font-semibold text-ink">{blueprint.headline}</div>
          <div className="mt-2 text-sm leading-6 text-slate-600">{blueprint.northStar}</div>
        </div>
        <div className="rounded-2xl bg-sand/80 px-4 py-2 text-sm font-semibold text-ink">
          {blueprint.currentPhaseLabel}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Blueprint summary")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{blueprint.strategicSummary}</div>
        </div>
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Learner snapshot")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{blueprint.learnerSnapshot}</div>
        </div>
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Route mode")}</div>
          <div className="mt-2 text-sm font-semibold text-ink">{blueprint.routeMode}</div>
        </div>
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Success signal")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{blueprint.successSignal}</div>
        </div>
      </div>

      {blueprint.focusPillars.length ? (
        <div className="space-y-3">
          <div className="text-sm font-semibold text-ink">{tr("Blueprint pillars")}</div>
          <div className="grid gap-3 md:grid-cols-3">
            {blueprint.focusPillars.slice(0, 3).map((pillar) => (
              <div key={pillar.id} className="rounded-2xl bg-accent/8 p-4">
                <div className="text-sm font-semibold text-ink">{pillar.title}</div>
                <div className="mt-2 text-sm leading-6 text-slate-700">{pillar.reason}</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        {blueprint.checkpoints.length ? (
          <div className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("What this blueprint is trying to unlock")}</div>
            <div className="mt-3 space-y-3">
              {blueprint.checkpoints.slice(0, 3).map((checkpoint) => (
                <div key={checkpoint.id} className="rounded-2xl bg-sand/80 p-3">
                  <div className="text-sm font-semibold text-ink">{checkpoint.title}</div>
                  <div className="mt-2 text-sm text-slate-700">{checkpoint.summary}</div>
                  <div className="mt-2 text-sm text-slate-600">{checkpoint.successSignal}</div>
                </div>
              ))}
            </div>
          </div>
        ) : null}
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-sm font-semibold text-ink">{tr("Liza's role in this plan")}</div>
          <div className="mt-2 text-sm leading-6 text-slate-700">{blueprint.lizaRole}</div>
          {blueprint.rhythmContract.length ? (
            <div className="mt-4">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Rhythm contract")}</div>
              <div className="mt-2 space-y-2 text-sm text-slate-700">
                {blueprint.rhythmContract.slice(0, 3).map((item) => (
                  <div key={item}>• {item}</div>
                ))}
              </div>
            </div>
          ) : null}
          {blueprint.guardrails.length ? (
            <div className="mt-4">
              <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Guardrails")}</div>
              <div className="mt-2 space-y-2 text-sm text-slate-700">
                {blueprint.guardrails.slice(0, 3).map((item) => (
                  <div key={item}>• {item}</div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </Card>
  );
}

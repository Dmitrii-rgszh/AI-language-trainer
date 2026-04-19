import type { DiagnosticRoadmap } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type ProgressDiagnosticSectionProps = {
  diagnosticRoadmap: DiagnosticRoadmap | null;
  expansionStageLabel?: string | null;
  hasAvailableDailyRoute?: boolean;
  onStartCheckpoint: () => Promise<void>;
  onStartPrimaryRoute?: (() => Promise<void>) | null;
  primaryRouteLabel?: string | null;
  roadmapSummary: string | null;
  tl: (values: string[]) => string;
  tr: (value: string) => string;
};

export function ProgressDiagnosticSection({
  diagnosticRoadmap,
  expansionStageLabel,
  hasAvailableDailyRoute,
  onStartCheckpoint,
  onStartPrimaryRoute,
  primaryRouteLabel,
  roadmapSummary,
  tl,
  tr,
}: ProgressDiagnosticSectionProps) {
  if (!diagnosticRoadmap) {
    return null;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-4">
        <div className="text-lg font-semibold text-ink">{tr("Level diagnostic")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {roadmapSummary ?? diagnosticRoadmap.summary}
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Declared")}: <span className="font-semibold text-ink">{diagnosticRoadmap.declaredCurrentLevel}</span>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Estimated")}: <span className="font-semibold text-ink">{diagnosticRoadmap.estimatedLevel}</span>
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Target")}: <span className="font-semibold text-ink">{diagnosticRoadmap.targetLevel}</span>
          </div>
        </div>
        <div className="text-sm text-slate-600">
          {tr("Overall score")}: {diagnosticRoadmap.overallScore}. {tr("Weakest skills")}:{" "}
          {tl(diagnosticRoadmap.weakestSkills)}.
        </div>
        {hasAvailableDailyRoute && onStartPrimaryRoute ? (
          <Button onClick={() => void onStartPrimaryRoute()}>
            {primaryRouteLabel ??
              (expansionStageLabel === tr("Ready for extension")
                ? tr("Continue broader route")
                : expansionStageLabel === tr("Stabilizing widening")
                  ? tr("Stabilize wider route")
                  : expansionStageLabel === tr("First widening pass")
                    ? tr("Start widening pass")
                    : tr("Start today’s route"))}
          </Button>
        ) : (
          <Button onClick={() => void onStartCheckpoint()}>{tr("Run diagnostic checkpoint")}</Button>
        )}
      </Card>

      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Roadmap milestones")}</div>
        {diagnosticRoadmap.milestones.map((milestone) => (
          <div key={milestone.level} className="rounded-2xl bg-white/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-ink">{milestone.level}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(milestone.status)}</div>
              </div>
              <div className="text-sm text-slate-600">
                {milestone.readiness}% {tr("ready")}
              </div>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-sand">
              <div className="h-full rounded-full bg-accent" style={{ width: `${milestone.readiness}%` }} />
            </div>
            <div className="mt-3 text-sm text-slate-600">{tr(milestone.description)}</div>
            <div className="mt-3 text-xs uppercase tracking-[0.14em] text-slate-500">
              {tr("Focus")}: {tl(milestone.focusSkills)}
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

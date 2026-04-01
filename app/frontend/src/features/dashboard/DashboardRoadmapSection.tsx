import { Link } from "react-router-dom";
import type { DiagnosticRoadmap } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardRoadmapSectionProps = {
  diagnosticRoadmap: DiagnosticRoadmap | null;
  onStartDiagnosticCheckpoint: () => Promise<void>;
  onStartRecoveryLesson: () => Promise<void>;
  roadmapSummary: string | null;
  tr: (value: string) => string;
};

export function DashboardRoadmapSection({
  diagnosticRoadmap,
  onStartDiagnosticCheckpoint,
  onStartRecoveryLesson,
  roadmapSummary,
  tr,
}: DashboardRoadmapSectionProps) {
  if (!diagnosticRoadmap) {
    return null;
  }

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Level roadmap")}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">
            {diagnosticRoadmap.estimatedLevel} {"->"} {diagnosticRoadmap.targetLevel}
          </div>
        </div>
        <Link
          to={routes.progress}
          className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
        >
          {tr("Open roadmap")}
        </Link>
      </div>
      <div className="text-sm leading-6 text-slate-600">{roadmapSummary}</div>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Declared level")}:{" "}
          <span className="font-semibold text-ink">{diagnosticRoadmap.declaredCurrentLevel}</span>
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Estimated level")}:{" "}
          <span className="font-semibold text-ink">{diagnosticRoadmap.estimatedLevel}</span>
        </div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Overall score")}: <span className="font-semibold text-ink">{diagnosticRoadmap.overallScore}</span>
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" onClick={() => void onStartDiagnosticCheckpoint()}>
          {tr("Run checkpoint")}
        </Button>
        <Button onClick={() => void onStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
      </div>
    </Card>
  );
}

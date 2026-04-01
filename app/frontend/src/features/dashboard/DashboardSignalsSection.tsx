import type { ProgressSnapshot } from "../../entities/progress/model";
import type { AdaptiveStudyLoop } from "../../shared/types/app-data";
import { Card } from "../../shared/ui/Card";

type DashboardSignalsSectionProps = {
  progress: ProgressSnapshot;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function DashboardSignalsSection({ progress, studyLoop, tr, tt }: DashboardSignalsSectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Listening contribution")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Listening score")}: <span className="font-semibold text-ink">{progress.listeningScore}</span>
        </div>
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {studyLoop?.listeningFocus
            ? `${tr("Adaptive loop is actively supporting listening around")} ${tt(studyLoop.listeningFocus)}.`
            : tr("Listening is not the primary recovery pressure right now.")}
        </div>
      </Card>
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Vocabulary contribution")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
          {tr("Due now")}: <span className="font-semibold text-ink">{studyLoop?.vocabularySummary.dueCount ?? 0}</span>
        </div>
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {studyLoop?.vocabularySummary.weakestCategory
            ? `${tr("Adaptive loop is currently surfacing more vocabulary from")} ${tt(studyLoop.vocabularySummary.weakestCategory)}.`
            : tr("Vocabulary load is balanced across categories right now.")}
        </div>
      </Card>
    </div>
  );
}

import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import type { DailyLoopPlan, LearnerJourneyState } from "../../shared/types/app-data";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardDailyLoopSectionProps = {
  dailyLoopPlan: DailyLoopPlan | null;
  journeyState: LearnerJourneyState | null;
  onStartDailyLoop: () => Promise<void>;
  tr: (value: string) => string;
};

export function DashboardDailyLoopSection({
  dailyLoopPlan,
  journeyState,
  onStartDailyLoop,
  tr,
}: DashboardDailyLoopSectionProps) {
  if (!dailyLoopPlan) {
    return null;
  }

  const tomorrowPreview = journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = journeyState?.strategySnapshot.sessionSummary ?? null;
  const practiceShiftLine = sessionSummary?.practiceMixEvaluation?.summaryLine ?? null;
  const tomorrowSignals = [
    tomorrowPreview?.carryOverSignalLabel
      ? `${tr("Carry forward")}: ${tomorrowPreview.carryOverSignalLabel}`
      : null,
    tomorrowPreview?.watchSignalLabel
      ? `${tr("Watch next")}: ${tomorrowPreview.watchSignalLabel}`
      : null,
  ].filter((item): item is string => Boolean(item));

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.22em] text-coral">{tr("Daily Loop")}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{dailyLoopPlan.headline}</div>
        </div>
        <div className="rounded-[22px] bg-white/72 px-4 py-3 text-sm text-slate-700">
          {`${dailyLoopPlan.estimatedMinutes} ${tr("minutes")}`}
        </div>
      </div>

      <div className="rounded-[24px] bg-sand/70 p-4 text-sm leading-6 text-slate-700">
        {dailyLoopPlan.summary}
      </div>

      {dailyLoopPlan.completedAt && tomorrowPreview ? (
        <div className="rounded-[24px] border border-accent/20 bg-accent/8 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-accent">{tr("Tomorrow preview")}</div>
          <div className="mt-2 text-lg font-semibold text-ink">{tomorrowPreview.headline}</div>
          <div className="mt-3 text-sm leading-6 text-slate-700">{tomorrowPreview.reason}</div>
          {practiceShiftLine ? (
            <div className="mt-3 rounded-[18px] bg-white/72 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">{tr("Practice shift")}:</span> {practiceShiftLine}
            </div>
          ) : null}
          {tomorrowSignals.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {tomorrowSignals.map((signal) => (
                <div
                  key={signal}
                  className="rounded-full border border-white/70 bg-white/74 px-3 py-1 text-xs font-semibold text-slate-700"
                >
                  {signal}
                </div>
              ))}
            </div>
          ) : null}
          <div className="mt-3 rounded-[18px] bg-white/70 p-3 text-sm text-slate-700">
            {tomorrowPreview.nextStepHint}
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-3">
        {dailyLoopPlan.steps.slice(0, 3).map((step) => (
          <div key={step.id} className="rounded-[22px] border border-white/70 bg-white/76 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{step.skill}</div>
            <div className="mt-2 text-sm font-semibold text-ink">{step.title}</div>
            <div className="mt-2 text-sm leading-6 text-slate-700">{step.description}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={() => void onStartDailyLoop()} disabled={dailyLoopPlan.completedAt !== null}>
          {dailyLoopPlan.lessonRunId ? tr("Resume today’s loop") : tr("Start today’s loop")}
        </Button>
        <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
          {tr("Open daily loop")}
        </Link>
      </div>
    </Card>
  );
}

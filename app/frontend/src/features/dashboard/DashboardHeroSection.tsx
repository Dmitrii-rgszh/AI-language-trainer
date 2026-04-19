import { Link } from "react-router-dom";
import type { DashboardData, MistakeResolutionSignal } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { buildRouteFollowUpHintFromState } from "../../shared/journey/route-entry-orchestration";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";

type DashboardHeroSectionProps = {
  dailyGoalProgress: number;
  dashboard: DashboardData;
  disabledProviders: number;
  fallbackProviders: number;
  onStartLesson: () => Promise<void>;
  primaryRouteLabel: string;
  primaryRouteSummary: string;
  readyProviders: number;
  recommendationGoal: string;
  recoveringSignals: MistakeResolutionSignal[];
  tl: (values: string[]) => string;
  totalProviders: number;
  tr: (value: string) => string;
};

export function DashboardHeroSection({
  dailyGoalProgress,
  dashboard,
  disabledProviders,
  fallbackProviders,
  onStartLesson,
  primaryRouteLabel,
  primaryRouteSummary,
  readyProviders,
  recommendationGoal,
  recoveringSignals,
  tl,
  totalProviders,
  tr,
}: DashboardHeroSectionProps) {
  const routeTitle = dashboard.dailyLoopPlan?.recommendedLessonTitle ?? dashboard.recommendation.title;
  const routeDuration = dashboard.dailyLoopPlan?.estimatedMinutes ?? dashboard.recommendation.duration;
  const routeFocus = dashboard.dailyLoopPlan?.focusArea ?? dashboard.recommendation.focusArea;
  const eyebrow = dashboard.dailyLoopPlan ? tr("Today's route") : tr("Recommended lesson");
  const routeRecoveryMemory = dashboard.journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = dashboard.journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = dashboard.journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const routeFollowUpMemory = dashboard.journeyState?.strategySnapshot.routeFollowUpMemory ?? null;
  const dayShape = dashboard.dailyLoopPlan
    ? describeRouteDayShape(
        dashboard.dailyLoopPlan,
        routeRecoveryMemory,
        routeReentryProgress,
        routeEntryMemory,
        tr,
      )
    : null;
  const routeFlowSummary =
    buildRouteFollowUpHintFromState(dashboard.dailyLoopPlan, dashboard.journeyState, tr) ?? primaryRouteSummary;

  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
            {eyebrow}
          </div>
          <div className="text-2xl font-[700] tracking-[-0.03em] text-ink">{tr(routeTitle)}</div>
          <div className="text-sm leading-6 text-slate-600">{recommendationGoal}</div>
          <div className="rounded-2xl bg-accent/8 p-4 text-sm text-slate-700">{primaryRouteSummary}</div>
          {routeFollowUpMemory?.summary || routeFollowUpMemory?.currentLabel || routeFollowUpMemory?.followUpLabel || dayShape ? (
            <div className="rounded-2xl border border-accent/15 bg-white/78 p-4 text-sm text-slate-700">
              <div className="text-[0.68rem] uppercase tracking-[0.18em] text-coral">{tr("Route flow")}</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {routeFollowUpMemory?.currentLabel ? (
                  <span className="rounded-full bg-accent/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-accent">
                    {tr("Now")}: {routeFollowUpMemory.currentLabel}
                  </span>
                ) : null}
                {routeFollowUpMemory?.followUpLabel ? (
                  <span className="rounded-full bg-coral/10 px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-coral">
                    {tr("Then")}: {routeFollowUpMemory.followUpLabel}
                  </span>
                ) : null}
                {dayShape?.substageLabel ? (
                  <span className="rounded-full bg-sand px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-ink">
                    {dayShape.substageLabel}
                  </span>
                ) : null}
                {dayShape?.expansionStageLabel ? (
                  <span className="rounded-full bg-white px-3 py-1 text-[0.72rem] font-[700] uppercase tracking-[0.14em] text-slate-600">
                    {dayShape.expansionStageLabel}
                  </span>
                ) : null}
              </div>
              <div className="mt-3 leading-6 text-slate-700">{routeFlowSummary}</div>
            </div>
          ) : null}
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Duration")}: {routeDuration} min. {tr("Focus")}:{" "}
            {tl(routeFocus.split(","))}.
          </div>
          {recoveringSignals.length > 0 ? (
            <div className="rounded-2xl bg-mint/30 p-4 text-sm text-slate-700">
              {tr("Recovery pressure is easing for")}{" "}
              {recoveringSignals.map((item) => tr(item.weakSpotTitle)).join(", ")}.{" "}
              {tr("The roadmap can lean back toward the main lesson flow.")}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button onClick={() => void onStartLesson()}>{primaryRouteLabel}</Button>
            <Link
              to={routes.progress}
              className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-[700] tracking-[-0.01em] text-ink transition-colors hover:bg-[#ddccb6]"
            >
              {tr("See progress")}
            </Link>
          </div>
        </Card>

        <Card className="grid gap-3 sm:grid-cols-2">
          <ScoreBadge label={tr("Grammar")} score={dashboard.progress.grammarScore} />
          <ScoreBadge label={tr("Speaking")} score={dashboard.progress.speakingScore} />
          <ScoreBadge label={tr("Writing")} score={dashboard.progress.writingScore} />
          <ScoreBadge label={tr("Profession")} score={dashboard.progress.professionScore} />
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{tr("Today")}</div>
          <div className="text-3xl font-[700] tracking-[-0.035em] text-ink">
            {dashboard.progress.minutesCompletedToday}/{dashboard.progress.dailyGoalMinutes} min
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-sand">
            <div className="h-full rounded-full bg-accent" style={{ width: `${dailyGoalProgress}%` }} />
          </div>
          <div className="text-sm text-slate-600">
            {tr("Daily goal completion")}: {dailyGoalProgress}%
          </div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
            {tr("Consistency")}
          </div>
          <div className="text-3xl font-[700] tracking-[-0.035em] text-ink">{dashboard.progress.streak} days</div>
          <div className="text-sm text-slate-600">
            {tr("Current streak and habit continuity across your recent sessions.")}
          </div>
        </Card>
        <Card className="space-y-3">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
            {tr("Runtime Stack")}
          </div>
          <div className="text-3xl font-[700] tracking-[-0.035em] text-ink">
            {readyProviders}/{totalProviders}
          </div>
          <div className="text-sm text-slate-600">
            {tr("Ready")}: {readyProviders}, {tr("fallback")}: {fallbackProviders}, {tr("offline")}:{" "}
            {disabledProviders}.
          </div>
        </Card>
      </div>
    </>
  );
}

import { Link } from "react-router-dom";
import type { DashboardData, MistakeResolutionSignal } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
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

  return (
    <>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">
            {eyebrow}
          </div>
          <div className="text-2xl font-[700] tracking-[-0.03em] text-ink">{tr(routeTitle)}</div>
          <div className="text-sm leading-6 text-slate-600">{recommendationGoal}</div>
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

import { Link } from "react-router-dom";
import type { AdaptiveStudyLoop } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type ActivityStudyLoopSectionProps = {
  expansionStageLabel?: string | null;
  hasAvailableDailyRoute: boolean;
  onStartPrimaryRoute: () => Promise<void>;
  onReviewVocabulary: (itemId: string) => Promise<void>;
  onStartRecoveryLesson: () => Promise<void>;
  primaryRouteLabel: string;
  reviewingVocabularyId: string | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ActivityStudyLoopSection({
  expansionStageLabel,
  hasAvailableDailyRoute,
  onStartPrimaryRoute,
  onReviewVocabulary,
  onStartRecoveryLesson,
  primaryRouteLabel,
  reviewingVocabularyId,
  studyLoop,
  tr,
  tt,
}: ActivityStudyLoopSectionProps) {
  if (!studyLoop) {
    return null;
  }

  const strategyAlignment = studyLoop.strategyAlignment ?? null;
  const prioritizedNextSteps =
    expansionStageLabel === tr("Ready for extension")
      ? [...studyLoop.nextSteps].sort((left, right) => {
          const leftScore = left.route === routes.activity ? 2 : left.route === routes.dailyLoop ? 1 : 0;
          const rightScore = right.route === routes.activity ? 2 : right.route === routes.dailyLoop ? 1 : 0;
          return rightScore - leftScore;
        })
      : expansionStageLabel === tr("Stabilizing widening") || expansionStageLabel === tr("First widening pass")
        ? [...studyLoop.nextSteps].sort((left, right) => {
            const leftScore = left.route === routes.dailyLoop ? 2 : left.route === routes.activity ? 1 : 0;
            const rightScore = right.route === routes.dailyLoop ? 2 : right.route === routes.activity ? 1 : 0;
            return rightScore - leftScore;
          })
        : studyLoop.nextSteps;

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Adaptive route summary")}</div>
        <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">{tr(studyLoop.summary)}</div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Due vocab")}: {studyLoop.vocabularySummary.dueCount}
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            Listening: {studyLoop.listeningFocus ? tt(studyLoop.listeningFocus) : tr("stable")}
          </div>
          <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
            {tr("Weak vocab cat")}:{" "}
            {studyLoop.vocabularySummary.weakestCategory ? tt(studyLoop.vocabularySummary.weakestCategory) : "balanced"}
          </div>
        </div>
        <div className="rounded-2xl bg-white/70 p-4">
          <div className="text-sm font-semibold text-ink">{tr("Why Liza shaped it this way")}</div>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {studyLoop.generationRationale.map((item) => (
              <div key={item}>• {tr(item)}</div>
            ))}
          </div>
        </div>
        {strategyAlignment ? (
          <div className="rounded-2xl border border-accent/20 bg-accent/8 p-4">
            <div className="text-sm font-semibold text-ink">{tr("How the route stays aligned")}</div>
            <div className="mt-3 text-sm leading-6 text-slate-700">{strategyAlignment.whyNow}</div>
            <div className="mt-3 rounded-2xl bg-white/78 p-4 text-sm text-slate-700">
              <span className="font-semibold text-ink">{tr("Route detail")}:</span> {strategyAlignment.routeSeedDetail}
            </div>
            {strategyAlignment.liveProgressFocus ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Live learner signal")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.liveProgressFocus}
                  {typeof strategyAlignment.liveProgressScore === "number" ? ` · ${strategyAlignment.liveProgressScore}/100` : ""}
                </div>
                <div className="mt-2 text-sm text-slate-700">
                  {strategyAlignment.liveProgressReason ?? strategyAlignment.recommendedModuleReason ?? strategyAlignment.nextBestAction}
                </div>
              </div>
            ) : null}
            {strategyAlignment.skillTrajectory ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Multi-day memory")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.skillTrajectory.focusSkill} · {strategyAlignment.skillTrajectory.direction}
                </div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.skillTrajectory.summary}</div>
              </div>
            ) : null}
            {strategyAlignment.strategyMemory ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Long strategy memory")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.strategyMemory.focusSkill} · {strategyAlignment.strategyMemory.persistenceLevel}
                </div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.strategyMemory.summary}</div>
              </div>
            ) : null}
            {strategyAlignment.routeCadenceMemory ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Route cadence")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.routeCadenceMemory.status}
                </div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.routeCadenceMemory.summary}</div>
              </div>
            ) : null}
            {strategyAlignment.routeRecoveryMemory ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Recovery arc")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.routeRecoveryMemory.phase}
                  {strategyAlignment.routeRecoveryMemory.focusSkill ? ` · ${strategyAlignment.routeRecoveryMemory.focusSkill}` : ""}
                </div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.routeRecoveryMemory.summary}</div>
              </div>
            ) : null}
            {strategyAlignment.routeReentryNextLabel ? (
              <div className="mt-3 rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Re-entry sequence")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">
                  {strategyAlignment.routeReentryNextLabel}
                  {typeof strategyAlignment.routeReentryCompletedSteps === "number" &&
                  typeof strategyAlignment.routeReentryTotalSteps === "number"
                    ? ` · ${strategyAlignment.routeReentryCompletedSteps}/${strategyAlignment.routeReentryTotalSteps}`
                    : ""}
                </div>
                <div className="mt-2 text-sm text-slate-700">
                  {strategyAlignment.recommendedModuleReason ?? strategyAlignment.nextBestAction}
                </div>
              </div>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-2">
              {strategyAlignment.carryOverSignalLabel ? (
                <div className="rounded-full bg-white/78 px-3 py-1 text-xs font-semibold text-slate-700">
                  {tr("Carry forward")}: {strategyAlignment.carryOverSignalLabel}
                </div>
              ) : null}
              {strategyAlignment.watchSignalLabel ? (
                <div className="rounded-full bg-white/78 px-3 py-1 text-xs font-semibold text-slate-700">
                  {tr("Watch next")}: {strategyAlignment.watchSignalLabel}
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
        {hasAvailableDailyRoute ? (
          <Button onClick={() => void onStartPrimaryRoute()}>{primaryRouteLabel}</Button>
        ) : (
          <Button onClick={() => void onStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
        )}
        {prioritizedNextSteps.map((step) => (
          <Link key={step.id} to={step.route} className="block rounded-2xl bg-sand/80 p-4">
            <div className="text-sm font-semibold text-ink">{tr(step.title)}</div>
            <div className="mt-2 text-sm text-slate-600">{tr(step.description)}</div>
          </Link>
        ))}
      </Card>

      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Vocabulary repetition")}</div>
          <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
            {studyLoop.dueVocabulary.length} {tr("due")}
          </div>
        </div>
        {studyLoop.dueVocabulary.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Vocabulary queue is clear for now.")}</div>
        ) : (
          studyLoop.dueVocabulary.map((item) => (
            <div key={item.id} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{item.word}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{item.translation}</div>
                </div>
                <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">{tt(item.learnedStatus)}</div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{item.context}</div>
              <div className="mt-4">
                <Button
                  className="rounded-full px-3 py-2 text-xs uppercase tracking-[0.12em]"
                  onClick={() => void onReviewVocabulary(item.id)}
                  disabled={reviewingVocabularyId === item.id}
                >
                  {reviewingVocabularyId === item.id ? tr("Saving...") : tr("Mark reviewed")}
                </Button>
              </div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

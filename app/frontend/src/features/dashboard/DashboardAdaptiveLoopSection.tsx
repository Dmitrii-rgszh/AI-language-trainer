import { Link } from "react-router-dom";
import type { AdaptiveStudyLoop, DailyLoopPlan } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardAdaptiveLoopSectionProps = {
  adaptiveHeadline: string | null;
  adaptiveSummary: string | null;
  dailyLoopPlan: DailyLoopPlan | null;
  onStartDailyRoute: () => Promise<void>;
  onReviewVocabulary: (itemId: string) => Promise<void>;
  onStartRecoveryLesson: () => Promise<void>;
  primaryRouteLabel: string;
  reviewingVocabularyId: string | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function DashboardAdaptiveLoopSection({
  adaptiveHeadline,
  adaptiveSummary,
  dailyLoopPlan,
  onStartDailyRoute,
  onReviewVocabulary,
  onStartRecoveryLesson,
  primaryRouteLabel,
  reviewingVocabularyId,
  studyLoop,
  tr,
  tt,
}: DashboardAdaptiveLoopSectionProps) {
  if (!studyLoop) {
    return null;
  }

  const dailyLoopSteps = [
    {
      id: "daily-loop-lesson",
      index: 1,
      title: tr("Core lesson"),
      description: tr(dailyLoopPlan?.recommendedLessonTitle ?? studyLoop.recommendation.title),
      detail: tr("Start with the central lesson so the rest of the session has a clear anchor."),
      route: dailyLoopPlan ? routes.dailyLoop : studyLoop.moduleRotation[0]?.route ?? routes.activity,
    },
    {
      id: "daily-loop-weakspot",
      index: 2,
      title: tr("Weak spot repair"),
      description: studyLoop.weakSpots[0]?.title ?? tr("No urgent weak spot"),
      detail: studyLoop.weakSpots[0]
        ? tr("Fix the most repeated weak point while the lesson context is still fresh.")
        : tr("Your weakest signal looks stable enough to keep the loop balanced today."),
      route: studyLoop.moduleRotation[0]?.route ?? routes.activity,
    },
    {
      id: "daily-loop-vocab",
      index: 3,
      title: tr("Vocabulary reinforcement"),
      description:
        studyLoop.dueVocabulary[0]?.word ??
        `${studyLoop.vocabularySummary.dueCount} ${tr("due cards")}`,
      detail: tr("Return one due word or phrase to active memory before finishing the session."),
      route: routes.vocabulary,
    },
    {
      id: "daily-loop-close",
      index: 4,
      title: tr("Close the loop"),
      description:
        studyLoop.nextSteps[0]?.title ??
        (studyLoop.listeningFocus ? tt(studyLoop.listeningFocus) : tr("Stabilize the next skill signal")),
      detail: tr("Finish with one targeted reinforcement step so the session lands as one connected system."),
      route: studyLoop.nextSteps[0]?.route ?? routes.activity,
    },
  ];
  const strategyAlignment = studyLoop.strategyAlignment ?? null;

  return (
    <div className="space-y-4">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">
              {tr("Today’s connected learning loop")}
            </div>
            <div className="mt-2 text-2xl font-semibold text-ink">
              {tr("One session, not separate modules")}
            </div>
          </div>
          <div className="rounded-2xl bg-sand/80 px-4 py-2 text-sm font-semibold text-ink">
            {dailyLoopSteps.length} {tr("steps")}
          </div>
        </div>
        <div className="text-sm leading-6 text-slate-600">
          {tr(
            "This is the first visible shape of the daily learning loop: one connected session that ties lesson work, weak spot repair, vocabulary memory, and the next reinforcement move together.",
          )}
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {dailyLoopSteps.map((step) => (
            <Link key={step.id} to={step.route} className="rounded-2xl bg-white/70 p-4 transition hover:bg-white">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent text-sm font-semibold text-white">
                  {step.index}
                </div>
                <div className="text-sm font-semibold text-ink">{step.title}</div>
              </div>
              <div className="mt-4 text-sm font-semibold text-slate-700">{step.description}</div>
              <div className="mt-2 text-sm leading-6 text-slate-600">{step.detail}</div>
            </Link>
          ))}
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="space-y-4">
        <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">
          {tr("Adaptive study loop")}
        </div>
        <div className="text-2xl font-semibold text-ink">{adaptiveHeadline}</div>
        <div className="text-sm leading-6 text-slate-600">{adaptiveSummary}</div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Due vocab")}: <span className="font-semibold text-ink">{studyLoop.vocabularySummary.dueCount}</span>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Active vocab")}:{" "}
            <span className="font-semibold text-ink">{studyLoop.vocabularySummary.activeCount}</span>
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Listening focus")}:{" "}
            <span className="font-semibold text-ink">
              {studyLoop.listeningFocus ? tt(studyLoop.listeningFocus) : tr("stable")}
            </span>
          </div>
        </div>
        <div className="rounded-2xl bg-sand/80 p-4">
          <div className="text-sm font-semibold text-ink">{tr("Why this loop was generated")}</div>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {studyLoop.generationRationale.map((item) => (
              <div key={item}>• {tr(item)}</div>
            ))}
          </div>
        </div>
        {strategyAlignment ? (
          <div className="rounded-2xl border border-accent/20 bg-accent/8 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Strategy alignment")}</div>
            <div className="mt-3 text-sm leading-6 text-slate-700">{strategyAlignment.whyNow}</div>
            <div className="mt-3 flex flex-wrap gap-2">
              <div className="rounded-full bg-white/78 px-3 py-1 text-xs font-semibold text-slate-700">
                {tr("Route seed")}: {strategyAlignment.routeSeedSource}
              </div>
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
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Route detail")}</div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.routeSeedDetail}</div>
              </div>
              <div className="rounded-2xl bg-white/78 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-slate-400">{tr("Recommended module")}</div>
                <div className="mt-2 text-sm font-semibold text-ink">{strategyAlignment.recommendedModuleKey ?? tr("main route")}</div>
                <div className="mt-2 text-sm text-slate-700">{strategyAlignment.recommendedModuleReason ?? strategyAlignment.nextBestAction}</div>
              </div>
            </div>
          </div>
        ) : null}
        {studyLoop.moduleRotation.length > 0 ? (
          <div className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Main flow rotation")}</div>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              {studyLoop.moduleRotation.slice(0, 3).map((item) => (
                <Link key={item.moduleKey} to={item.route} className="rounded-2xl bg-sand/80 p-4">
                  <div className="text-xs uppercase tracking-[0.16em] text-coral">
                    {tr("priority")} {item.priority}
                  </div>
                  <div className="mt-2 text-sm font-semibold text-ink">{tr(item.title)}</div>
                  <div className="mt-2 text-sm text-slate-600">{tr(item.reason)}</div>
                </Link>
              ))}
            </div>
          </div>
        ) : null}
        <div className="flex flex-wrap gap-3">
          <Button onClick={() => void onStartDailyRoute()}>{primaryRouteLabel}</Button>
          <Button variant="secondary" onClick={() => void onStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
          <Link
            to={routes.activity}
            className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
          >
            {tr("Open full loop")}
          </Link>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {studyLoop.nextSteps.map((step) => (
            <Link key={step.id} to={step.route} className="rounded-2xl bg-white/70 p-4">
              <div className="text-sm font-semibold text-ink">{tr(step.title)}</div>
              <div className="mt-2 text-xs uppercase tracking-[0.16em] text-coral">{tt(step.stepType)}</div>
              <div className="mt-3 text-sm text-slate-600">{tr(step.description)}</div>
            </Link>
          ))}
        </div>
      </Card>

        <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Vocabulary due now")}</div>
          <div className="text-xs uppercase tracking-[0.16em] text-slate-500">
            {studyLoop.dueVocabulary.length} {tr("cards")}
          </div>
        </div>
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {tr("Queue balance")}: {studyLoop.vocabularySummary.newCount} {tr("new")},{" "}
          {studyLoop.vocabularySummary.activeCount} {tr("active")}, {studyLoop.vocabularySummary.masteredCount}{" "}
          {tr("mastered")}.
          {studyLoop.vocabularySummary.weakestCategory
            ? ` ${tr("Most loaded category")}: ${tt(studyLoop.vocabularySummary.weakestCategory)}.`
            : ""}
        </div>
        {studyLoop.dueVocabulary.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("No urgent vocabulary reviews right now. Stay with the current lesson flow.")}
          </div>
        ) : (
          studyLoop.dueVocabulary.map((item) => (
            <div key={item.id} className="rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{item.word}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{item.translation}</div>
                </div>
                <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                  {tr("stage")} {item.repetitionStage}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{item.context}</div>
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  variant="secondary"
                  onClick={() => void onReviewVocabulary(item.id)}
                  disabled={reviewingVocabularyId === item.id}
                >
                  {reviewingVocabularyId === item.id ? tr("Saving...") : tr("Mark reviewed")}
                </Button>
                <Link
                  to={routes.activity}
                  className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
                >
                  {tr("Open activity")}
                </Link>
              </div>
            </div>
          ))
        )}
        </Card>
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import type { AdaptiveStudyLoop } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type DashboardAdaptiveLoopSectionProps = {
  adaptiveHeadline: string | null;
  adaptiveSummary: string | null;
  onReviewVocabulary: (itemId: string) => Promise<void>;
  onStartRecoveryLesson: () => Promise<void>;
  reviewingVocabularyId: string | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function DashboardAdaptiveLoopSection({
  adaptiveHeadline,
  adaptiveSummary,
  onReviewVocabulary,
  onStartRecoveryLesson,
  reviewingVocabularyId,
  studyLoop,
  tr,
  tt,
}: DashboardAdaptiveLoopSectionProps) {
  if (!studyLoop) {
    return null;
  }

  return (
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
          <Button onClick={() => void onStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
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
  );
}

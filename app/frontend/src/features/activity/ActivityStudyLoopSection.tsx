import { Link } from "react-router-dom";
import type { AdaptiveStudyLoop } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type ActivityStudyLoopSectionProps = {
  onReviewVocabulary: (itemId: string) => Promise<void>;
  onStartRecoveryLesson: () => Promise<void>;
  reviewingVocabularyId: string | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ActivityStudyLoopSection({
  onReviewVocabulary,
  onStartRecoveryLesson,
  reviewingVocabularyId,
  studyLoop,
  tr,
  tt,
}: ActivityStudyLoopSectionProps) {
  if (!studyLoop) {
    return null;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
      <Card className="space-y-3">
        <div className="text-lg font-semibold text-ink">{tr("Adaptive loop summary")}</div>
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
          <div className="text-sm font-semibold text-ink">{tr("Generation rationale")}</div>
          <div className="mt-3 space-y-2 text-sm text-slate-600">
            {studyLoop.generationRationale.map((item) => (
              <div key={item}>• {tr(item)}</div>
            ))}
          </div>
        </div>
        <Button onClick={() => void onStartRecoveryLesson()}>{tr("Start recovery lesson")}</Button>
        {studyLoop.nextSteps.map((step) => (
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

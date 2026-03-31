import { Link, Navigate, useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";
import { SectionHeading } from "../../shared/ui/SectionHeading";

function deltaLabel(before: number | undefined, after: number, tr: (value: string) => string) {
  if (before === undefined) {
    return `${tr("now")} ${after}`;
  }

  const delta = after - before;
  if (delta > 0) {
    return `+${delta}`;
  }
  if (delta < 0) {
    return `${delta}`;
  }
  return tr("no change");
}

export function LessonResultsScreen() {
  const { tr, formatDateTime } = useLocale();
  const result = useAppStore((state) => state.lastLessonResult);
  const dashboard = useAppStore((state) => state.dashboard);
  const startLesson = useAppStore((state) => state.startLesson);
  const startRecoveryLesson = useAppStore((state) => state.startRecoveryLesson);
  const navigate = useNavigate();

  if (!result) {
    return <Navigate to={routes.dashboard} replace />;
  }

  const handleContinueRoadmap = async () => {
    if (dashboard?.recommendation.lessonType === "recovery") {
      await startRecoveryLesson();
    } else {
      await startLesson();
    }
    navigate(routes.lessonRunner);
  };
  const diagnosticMilestoneDeltas =
    result.milestoneDeltas?.filter((item) => item.readinessAfter !== item.readinessBefore) ?? [];
  const isCheckpointResult = result.title.toLowerCase().includes("checkpoint");

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Results")}
        title={tr(result.title)}
        description={tr("Итоги lesson run: score, найденные ошибки, обновление progress и следующий рекомендуемый шаг.")}
      />

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Lesson summary")}</div>
          {isCheckpointResult ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              {tr("Diagnostic checkpoint completed. Your roadmap and next focus should now be refreshed from this control run.")}
            </div>
          ) : null}
          <div className="text-3xl font-semibold text-ink">{result.score}/100</div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Completed blocks")}: {result.completedBlocks}/{result.totalBlocks}
          </div>
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
            {tr("Completed at")}: {result.completedAt ? formatDateTime(result.completedAt) : tr("just now")}
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              to={routes.dashboard}
              className="rounded-2xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-teal-700"
            >
              {tr("Back to dashboard")}
            </Link>
            <Link
              to={routes.progress}
              className="rounded-2xl bg-sand px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-[#ddccb6]"
            >
              {tr("See progress")}
            </Link>
          </div>
        </Card>

        <Card className="grid gap-3 sm:grid-cols-2">
          <ScoreBadge
            label={`${tr("Grammar")} ${deltaLabel(result.progressBefore?.grammarScore, result.progressAfter.grammarScore, tr)}`}
            score={result.progressAfter.grammarScore}
          />
          <ScoreBadge
            label={`${tr("Speaking")} ${deltaLabel(result.progressBefore?.speakingScore, result.progressAfter.speakingScore, tr)}`}
            score={result.progressAfter.speakingScore}
          />
          <ScoreBadge
            label={`${tr("Writing")} ${deltaLabel(result.progressBefore?.writingScore, result.progressAfter.writingScore, tr)}`}
            score={result.progressAfter.writingScore}
          />
          <ScoreBadge
            label={`${tr("Profession")} ${deltaLabel(result.progressBefore?.professionScore, result.progressAfter.professionScore, tr)}`}
            score={result.progressAfter.professionScore}
          />
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Detected mistakes")}</div>
          {result.mistakes.length > 0 ? (
            result.mistakes.slice(0, 5).map((mistake) => (
              <div key={mistake.id} className="rounded-2xl bg-white/70 p-4">
                <div className="text-sm font-semibold text-ink">{tr(mistake.subtype)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(mistake.category)}</div>
                <div className="mt-3 text-sm text-slate-700">{tr("Original")}: {mistake.originalText}</div>
                <div className="mt-2 text-sm text-slate-700">{tr("Fix")}: {mistake.correctedText}</div>
                <div className="mt-2 text-sm text-slate-600">{tr(mistake.explanation)}</div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("No new mistakes were detected in this run.")}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="text-lg font-semibold text-ink">{tr("Next recommended step")}</div>
          <div className="rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{result.nextRecommendationTitle ? tr(result.nextRecommendationTitle) : tr("Next lesson")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {result.nextRecommendationGoal ? tr(result.nextRecommendationGoal) : tr("Открой dashboard для следующей персональной рекомендации.")}
            </div>
          </div>
          {dashboard?.studyLoop ? (
            <div className="rounded-2xl bg-sand/80 p-4">
              <div className="text-sm font-semibold text-ink">{tr(dashboard.studyLoop.headline)}</div>
              <div className="mt-2 text-sm text-slate-600">{tr(dashboard.studyLoop.summary)}</div>
            </div>
          ) : null}
          <Button onClick={() => void handleContinueRoadmap()}>{tr("Continue personal roadmap")}</Button>
          <Link
            to={routes.dashboard}
            className="block rounded-2xl bg-white/70 p-4 text-sm font-semibold text-ink transition-colors hover:bg-white"
          >
            {tr("Open dashboard recommendation")}
          </Link>
          <Button onClick={() => window.history.back()} variant="ghost">
            {tr("Back")}
          </Button>
        </Card>
      </div>

      {isCheckpointResult ? (
        <Card className="space-y-4">
          <div className="text-lg font-semibold text-ink">{tr("Checkpoint impact on roadmap")}</div>
          <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="space-y-3">
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Estimated level")}:{" "}
                <span className="font-semibold text-ink">
                  {result.diagnosticEstimatedLevelBefore ?? "n/a"} {"->"} {result.diagnosticEstimatedLevelAfter ?? "n/a"}
                </span>
              </div>
              <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                {tr("Overall diagnostic score")}:{" "}
                <span className="font-semibold text-ink">
                  {result.diagnosticOverallScoreBefore ?? 0} {"->"} {result.diagnosticOverallScoreAfter ?? 0}
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Listening")} {deltaLabel(result.progressBefore?.listeningScore, result.progressAfter.listeningScore, tr)}
                </div>
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Pronunciation")}{" "}
                  {deltaLabel(result.progressBefore?.pronunciationScore, result.progressAfter.pronunciationScore, tr)}
                </div>
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Writing")} {deltaLabel(result.progressBefore?.writingScore, result.progressAfter.writingScore, tr)}
                </div>
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Grammar")} {deltaLabel(result.progressBefore?.grammarScore, result.progressAfter.grammarScore, tr)}
                </div>
                <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
                  {tr("Speaking")} {deltaLabel(result.progressBefore?.speakingScore, result.progressAfter.speakingScore, tr)}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {result.checkpointSkillInsights?.map((insight) => (
                <div key={insight.skill} className="rounded-2xl border border-sand bg-sand/60 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-ink">{tr(insight.skill)} {tr("checkpoint")}</div>
                    <div className="text-sm text-slate-600">{tr("score")} {insight.checkpointScore}/100</div>
                  </div>
                  <div className="mt-3 text-sm text-slate-600">{insight.note}</div>
                  {insight.skill === "Pronunciation" ? (
                    <div className="mt-3 rounded-2xl bg-white/70 p-3 text-sm text-slate-600">
                      {tr("This score now reflects word-level matching and sound-focus checks, not just a generic voice proxy.")}
                    </div>
                  ) : null}
                </div>
              ))}
              {diagnosticMilestoneDeltas.length > 0 ? (
                diagnosticMilestoneDeltas.map((item) => (
                  <div key={item.level} className="rounded-2xl bg-white/70 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-ink">{item.level} {tr("readiness")}</div>
                      <div className="text-sm text-slate-600">
                        {item.readinessBefore}% {"->"} {item.readinessAfter}%
                      </div>
                    </div>
                    <div className="mt-3 text-sm text-slate-600">
                      {item.readinessAfter > item.readinessBefore
                        ? tr("Checkpoint performance pulled this milestone upward.")
                        : tr("Checkpoint performance exposed a weaker area and reduced readiness.")}
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
                  {tr("This checkpoint confirmed the current roadmap without changing milestone readiness.")}
                </div>
              )}
            </div>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

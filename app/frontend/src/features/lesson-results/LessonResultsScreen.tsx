import { Link, Navigate, useNavigate } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";
import { ScoreBadge } from "../../shared/ui/ScoreBadge";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LizaGuidanceGrid } from "../../widgets/liza/LizaGuidanceGrid";
import { JourneySessionSummaryPanel } from "../../widgets/journey/JourneySessionSummaryPanel";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

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
  const { tr, formatDateTime, locale } = useLocale();
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
  const currentFocusArea = dashboard?.journeyState?.currentFocusArea ?? dashboard?.dailyLoopPlan?.focusArea ?? "next step";
  const coachMessage =
    locale === "ru"
      ? `Сессия завершена. Сейчас важно не просто посмотреть на score, а понять, как этот результат сдвинул твой маршрут вокруг ${currentFocusArea} и что я рекомендую следующим шагом.`
      : `The session is complete. What matters now is not only the score, but how this result shifted your route around ${currentFocusArea} and what I recommend next.`;
  const coachSupportingText =
    dashboard?.journeyState?.currentStrategySummary ??
    (locale === "ru"
      ? "Lesson results должны закрывать сессию не сухими цифрами, а понятным объяснением: что получилось, что просело и как это меняет следующий шаг."
      : "Lesson results should close the session with more than dry numbers. They should explain what worked, what slipped, and how that changes the next step.");
  const nextResultStep =
    dashboard?.journeyState?.nextBestAction ??
    result.nextRecommendationGoal ??
    (locale === "ru"
      ? "Открой dashboard и запусти следующий guided step, чтобы не терять continuity."
      : "Open the dashboard and launch the next guided step so continuity stays intact.");
  const tomorrowPreview = dashboard?.journeyState?.strategySnapshot.tomorrowPreview ?? null;
  const sessionSummary = dashboard?.journeyState?.strategySnapshot.sessionSummary ?? null;
  const strongestShift = [
    {
      label: tr("Grammar"),
      delta: (result.progressAfter.grammarScore ?? 0) - (result.progressBefore?.grammarScore ?? 0),
    },
    {
      label: tr("Speaking"),
      delta: (result.progressAfter.speakingScore ?? 0) - (result.progressBefore?.speakingScore ?? 0),
    },
    {
      label: tr("Writing"),
      delta: (result.progressAfter.writingScore ?? 0) - (result.progressBefore?.writingScore ?? 0),
    },
    {
      label: tr("Profession"),
      delta: (result.progressAfter.professionScore ?? 0) - (result.progressBefore?.professionScore ?? 0),
    },
  ].sort((left, right) => right.delta - left.delta)[0];
  const explainActions = [
    {
      id: "results-simpler",
      label: locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        isCheckpointResult
          ? sessionSummary?.headline ??
            (locale === "ru"
              ? "Checkpoint закончен: теперь система точнее понимает твой уровень и может перестроить следующий маршрут."
              : "The checkpoint is done: the system now understands your level more precisely and can reshape the next route.")
          : sessionSummary?.headline ??
            (locale === "ru"
              ? "Сессия завершена: система обновила ошибки, progress и следующий маршрут. Теперь задача не пересматривать всё подряд, а пойти в следующий осмысленный шаг."
              : "The session is complete: the system updated mistakes, progress, and the next route. The goal now is not to re-read everything, but to move into the next meaningful step."),
    },
    {
      id: "results-why",
      label: locale === "ru" ? "Почему это важно" : "Why it matters",
      text:
        sessionSummary?.whatWorked ??
        (strongestShift.delta !== 0
          ? locale === "ru"
            ? `Потому что именно сдвиг в ${strongestShift.label} показывает, что эта сессия реально изменила learner model, а не просто закрыла ещё один урок.`
            : `Because the shift in ${strongestShift.label} shows that this session changed the learner model rather than just closing another lesson.`
          : locale === "ru"
            ? "Потому что даже без большого score-jump система уточнила слабые сигналы и стала точнее в выборе следующего шага."
            : "Because even without a large score jump, the system refined the weak signals and became more precise about the next step."),
    },
    {
      id: "results-priority",
      label: locale === "ru" ? "Что теперь главное" : "What matters now",
      text:
        sessionSummary?.watchSignal ??
        (locale === "ru"
          ? `Сейчас главное - не потерять continuity: принять updated route вокруг ${currentFocusArea} и не откатываться в случайный выбор следующего модуля.`
          : `What matters now is not losing continuity: accept the updated route around ${currentFocusArea} and avoid falling back into random module hopping.`),
    },
    {
      id: "results-next",
      label: locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: sessionSummary?.strategyShift ?? tomorrowPreview?.nextStepHint ?? nextResultStep,
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Results")}
        title={tr(result.title)}
        description={tr("Итоги lesson run: score, найденные ошибки, обновление progress и следующий рекомендуемый шаг.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.lessonResultsCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`lesson-results:${result.runId}:${result.score}:${currentFocusArea}`}
          title={tr("Liza Results Layer")}
          message={coachMessage}
          spokenMessage={coachMessage}
          spokenLanguage={locale}
          replayCta={tr("Послушать ещё раз")}
          primaryAction={<Button onClick={() => void handleContinueRoadmap()} className="proof-lesson-primary-button">{tr("Продолжить roadmap")}</Button>}
          secondaryAction={(
            <Link to={routes.dashboard} className="proof-lesson-secondary-action">
              {tr("Открыть dashboard")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <LizaGuidanceGrid
        currentLabel={locale === "ru" ? "Что сейчас происходит" : "What is happening now"}
        currentText={
          locale === "ru"
            ? `Урок завершён со score ${result.score}/100. Система уже собрала ошибки, обновила progress и пересчитала следующий шаг.`
            : `The lesson finished with a ${result.score}/100 score. The system has already collected mistakes, refreshed progress, and recalculated the next step.`
        }
        whyLabel={locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          locale === "ru"
            ? strongestShift.delta !== 0
              ? `Сильнее всего сейчас сдвинулся сигнал ${strongestShift.label} (${strongestShift.delta > 0 ? `+${strongestShift.delta}` : strongestShift.delta}). Именно такие сдвиги меняют реальную стратегию, а не просто историю уроков.`
              : "Даже если большие score-сдвиги ещё не видны, эта сессия всё равно уточняет roadmap и повышает точность следующего шага."
            : strongestShift.delta !== 0
              ? `The strongest shift right now is ${strongestShift.label} (${strongestShift.delta > 0 ? `+${strongestShift.delta}` : strongestShift.delta}). These shifts change the real strategy, not just the lesson history.`
              : "Even if large score shifts are not visible yet, this session still sharpens the roadmap and improves the next step."
        }
        nextLabel={locale === "ru" ? "Что делать дальше" : "What to do next"}
        nextText={nextResultStep}
      />

      <LizaExplainActions
        title={locale === "ru" ? "Разобрать итог с Лизой" : "Break down the result with Liza"}
        actions={explainActions}
      />

      {sessionSummary ? (
        <JourneySessionSummaryPanel
          summary={sessionSummary}
          title={tr("Session shift")}
          tr={tr}
        />
      ) : null}

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
          {dashboard?.dailyLoopPlan?.completedAt ? (
            <div className="rounded-2xl bg-accent/10 p-4 text-sm text-accent">
              {tr("Today's daily loop is now marked as completed. Review the updated next step before you launch the next session.")}
            </div>
          ) : null}
          {tomorrowPreview ? (
            <div className="rounded-2xl border border-accent/20 bg-white/76 p-4">
              <div className="text-xs uppercase tracking-[0.16em] text-accent">{tr("Tomorrow preview")}</div>
              <div className="mt-2 text-sm font-semibold text-ink">{tomorrowPreview.headline}</div>
              <div className="mt-2 text-sm text-slate-600">{tomorrowPreview.reason}</div>
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

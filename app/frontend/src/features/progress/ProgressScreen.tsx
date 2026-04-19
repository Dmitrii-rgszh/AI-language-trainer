import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { ProgressDiagnosticSection } from "./ProgressDiagnosticSection";
import { ProgressHistorySection } from "./ProgressHistorySection";
import { ProgressOverviewSection } from "./ProgressOverviewSection";
import { ProgressPronunciationSection } from "./ProgressPronunciationSection";
import { ProgressSignalsSection } from "./ProgressSignalsSection";
import { useProgressScreen } from "./useProgressScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LizaGuidanceGrid } from "../../widgets/liza/LizaGuidanceGrid";
import { RouteIntelligencePanel } from "../../widgets/journey/RouteIntelligencePanel";

export function ProgressScreen() {
  const progressView = useProgressScreen();

  if (!progressView.progress) {
    return <Card>{progressView.tr("Подгружаю progress...")}</Card>;
  }

  const currentFocusArea =
    progressView.dashboard?.journeyState?.currentFocusArea ??
    progressView.dashboard?.dailyLoopPlan?.focusArea ??
    progressView.studyLoop?.focusArea ??
    "progress";
  const journeyState = progressView.dashboard?.journeyState ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape =
    progressView.dashboard?.dailyLoopPlan
      ? describeRouteDayShape(
          progressView.dashboard.dailyLoopPlan,
          routeRecoveryMemory,
          routeReentryProgress,
          routeEntryMemory,
          progressView.tr,
        )
      : null;
  const coachMessage =
    progressView.locale === "ru"
      ? progressView.hasAvailableDailyRoute
        ? dayShape
          ? `Здесь я не просто показываю цифры. Я сверяю, как текущий фокус ${currentFocusArea} должен повлиять на сегодняшнюю route через skill progress, roadmap и свежие сигналы. Сегодня это ${dayShape.title}, поэтому progress должен объяснять именно этот ритм дня.`
          : `Здесь я не просто показываю цифры. Я сверяю, как текущий фокус ${currentFocusArea} должен повлиять на сегодняшнюю route через skill progress, roadmap и свежие сигналы.`
        : `Здесь я не просто показываю цифры. Я сверяю, как твой текущий фокус ${currentFocusArea} отражается в skill progress, diagnostic roadmap и recent activity.`
      : progressView.hasAvailableDailyRoute
        ? dayShape
          ? `I do not show numbers here for their own sake. I compare how the current ${currentFocusArea} focus should shape today's route through skill progress, the roadmap, and fresh signals. Today is a ${dayShape.title}, so progress has to explain that rhythm clearly.`
          : `I do not show numbers here for their own sake. I compare how the current ${currentFocusArea} focus should shape today's route through skill progress, the roadmap, and fresh signals.`
        : `I do not show numbers here for their own sake. I compare how your current ${currentFocusArea} focus appears across skill progress, the diagnostic roadmap, and recent activity.`;
  const coachSupportingText =
    (dayShape
      ? `${journeyState?.currentStrategySummary ?? progressView.routePriorityView.summary ?? ""} ${progressView.tr("Day shape")}: ${dayShape.title}. ${dayShape.summary}${dayShape.expansionStageLabel ? ` ${progressView.tr("Expansion stage")}: ${dayShape.expansionStageLabel}.` : ""}${dayShape.expansionWindowLabel ? ` ${dayShape.expansionWindowLabel}.` : ""}`.trim()
      : null) ??
    progressView.dashboard?.journeyState?.currentStrategySummary ??
    progressView.routePriorityView.summary ??
    (progressView.locale === "ru"
      ? "Прогресс должен объяснять не только сколько процентов стало лучше, но и почему система смещает следующий шаг именно так."
      : "Progress should explain not only how many points improved, but also why the system is shifting the next step this way.");
  const nextProgressStep =
    progressView.dashboard?.journeyState?.nextBestAction ??
    progressView.routePriorityView.summary ??
    (progressView.hasAvailableDailyRoute
      ? dayShape
        ? progressView.locale === "ru"
          ? `Сверь roadmap и свежие сигналы, затем вернись в сегодняшнюю route: это ${dayShape.title}${dayShape.expansionStageLabel ? `, этап ${dayShape.expansionStageLabel.toLowerCase()}` : ""}, и следующий практический шаг должен остаться в её ритме.`
          : `Compare the roadmap with fresh signals, then return to today's route. This is a ${dayShape.title}${dayShape.expansionStageLabel ? ` in the ${dayShape.expansionStageLabel.toLowerCase()} phase` : ""}, and the next practical move should stay inside that rhythm.`
        : progressView.locale === "ru"
          ? "Сверь roadmap и свежие сигналы, затем вернись в сегодняшнюю route: именно она должна превратить выводы progress в следующий практический шаг."
          : "Compare the roadmap with fresh signals, then return to today's route. That route should turn progress into the next practical move."
      : progressView.locale === "ru"
        ? "Сравни roadmap и свежие сигналы, затем открой daily loop или checkpoint, если нужен более точный срез."
        : "Compare the roadmap with fresh signals, then open the daily loop or checkpoint if you need a sharper read.");
  const explainActions = [
    {
      id: "progress-simpler",
      label: progressView.locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        progressView.locale === "ru"
          ? "Этот экран нужен, чтобы понять направление, а не просто посмотреть цифры. Если направление ясное, следующий шаг тоже становится яснее."
          : "This screen is here to explain direction, not just numbers. Once the direction is clear, the next step becomes clearer too.",
    },
    {
      id: "progress-why",
      label: progressView.locale === "ru" ? "Почему это важно" : "Why it matters",
      text: coachSupportingText,
    },
    {
      id: "progress-priority",
      label: progressView.locale === "ru" ? "Что важнее всего" : "What matters most",
      text:
        progressView.hasAvailableDailyRoute
          ? progressView.locale === "ru"
            ? `Сейчас важнее всего понять, стабилизируется ли ${currentFocusArea}${dayShape?.expansionStageLabel ? ` на этапе ${dayShape.expansionStageLabel.toLowerCase()}` : ""} и как это должно поменять сегодняшнюю route.`
            : `What matters most right now is whether ${currentFocusArea} is stabilizing${dayShape?.expansionStageLabel ? ` during the ${dayShape.expansionStageLabel.toLowerCase()} phase` : ""} and how that should reshape today's route.`
          : progressView.locale === "ru"
            ? `Сейчас важнее всего понять, стабилизируется ли ${currentFocusArea} и есть ли смысл идти в guided loop или в checkpoint.`
            : `What matters most right now is whether ${currentFocusArea} is stabilizing and whether the better move is a guided loop or a checkpoint.`,
    },
    {
      id: "progress-next",
      label: progressView.locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: nextProgressStep,
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={progressView.tr("Progress")}
        title={progressView.tr("Skill Progress")}
        description={progressView.tr("Follow your scores, recent practice, and roadmap shifts in one view.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.progressCoach}>
        <LizaCoachPanel
          locale={progressView.locale}
          playKey={`progress:${currentFocusArea}:${progressView.progress.id}:${progressView.progress.streak}`}
          title={progressView.tr("Liza Progress Layer")}
          message={coachMessage}
          spokenMessage={coachMessage}
          spokenLanguage={progressView.locale}
          replayCta={progressView.tr("Послушать ещё раз")}
          primaryAction={(
            <Button type="button" onClick={() => void progressView.handleStartPrimaryRoute()} className="proof-lesson-primary-button">
              {progressView.primaryRouteLabel}
            </Button>
          )}
          secondaryAction={(
            <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
              {progressView.hasAvailableDailyRoute
                ? progressView.tr("Открыть route details")
                : progressView.tr("Открыть daily loop")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <LizaGuidanceGrid
        currentLabel={progressView.locale === "ru" ? "Что сейчас происходит" : "What is happening now"}
        currentText={
          progressView.locale === "ru"
            ? dayShape
              ? `Этот экран собирает scores, roadmap shifts, recent lesson history и pronunciation/listening signals в одну читаемую картину. Сегодня маршрут идёт как ${dayShape.title}, поэтому progress должен показывать не только результат, но и форму дня.`
              : "Этот экран собирает scores, roadmap shifts, recent lesson history и pronunciation/listening signals в одну читаемую картину."
            : dayShape
              ? `This screen brings scores, roadmap shifts, recent lesson history, and pronunciation/listening signals into one readable picture. Today's route is a ${dayShape.title}, so progress has to show not only the result, but the shape of the day.`
              : "This screen brings scores, roadmap shifts, recent lesson history, and pronunciation/listening signals into one readable picture."
        }
        whyLabel={progressView.locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          progressView.locale === "ru"
            ? dayShape
              ? `Тебе важно видеть не только итог, но и направление: укрепляется ли ${currentFocusArea}, стабилизируется ли roadmap и почему система выбрала именно ${dayShape.title} как форму сегодняшнего шага.`
              : `Тебе важно видеть не только итог, но и направление: укрепляется ли ${currentFocusArea}, стабилизируется ли roadmap и какие слабые места всё ещё тянут назад.`
            : dayShape
              ? `You need to see not only the result, but the direction: whether ${currentFocusArea} is getting stronger, whether the roadmap is stabilizing, and why the system chose ${dayShape.title} as the shape of today.`
              : `You need to see not only the result, but the direction: whether ${currentFocusArea} is getting stronger, whether the roadmap is stabilizing, and which weak spots still pull things back.`
        }
        nextLabel={progressView.locale === "ru" ? "Что делать дальше" : "What to do next"}
        nextText={nextProgressStep}
      />

      <LizaExplainActions
        title={progressView.locale === "ru" ? "Разобрать progress с Лизой" : "Break down progress with Liza"}
        actions={explainActions}
      />

      <LivingDepthSection id={livingDepthSectionIds.progressDiagnostic}>
        <ProgressDiagnosticSection
          diagnosticRoadmap={progressView.diagnosticRoadmap}
          expansionStageLabel={dayShape?.expansionStageLabel ?? null}
          hasAvailableDailyRoute={progressView.hasAvailableDailyRoute}
          onStartCheckpoint={progressView.handleStartCheckpoint}
          onStartPrimaryRoute={progressView.handleStartPrimaryRoute}
          primaryRouteLabel={progressView.primaryRouteLabel}
          roadmapSummary={progressView.roadmapSummary}
          tl={progressView.tl}
          tr={progressView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressOverview}>
        <ProgressOverviewSection
          averageLessonScore={progressView.averageLessonScore}
          dailyGoalProgress={progressView.dailyGoalProgress}
          formatDate={progressView.formatDate}
          formatDays={progressView.formatDays}
          mostRecentLesson={progressView.mostRecentLesson}
          progress={progressView.progress}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>

      <RouteIntelligencePanel
        dailyLoopPlan={progressView.dashboard?.dailyLoopPlan ?? null}
        journeyState={progressView.dashboard?.journeyState ?? null}
        title={progressView.tr("Route intelligence")}
        tr={progressView.tr}
      />

      <LivingDepthSection id={livingDepthSectionIds.progressPronunciation}>
        <ProgressPronunciationSection
          progress={progressView.progress}
          pronunciationTrend={progressView.pronunciationTrend}
          tr={progressView.tr}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressHistory}>
        <ProgressHistorySection
          activityError={progressView.activityError}
          feedbackSourceLabel={progressView.feedbackSourceLabel}
          formatDate={progressView.formatDate}
          formatDateTime={progressView.formatDateTime}
          progress={progressView.progress}
          recentSpeakingAttempts={progressView.recentSpeakingAttempts}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.progressSignals}>
        <ProgressSignalsSection
          formatDays={progressView.formatDays}
          listeningAttempts={progressView.listeningAttempts}
          listeningTrend={progressView.listeningTrend}
          studyLoop={progressView.studyLoop}
          tr={progressView.tr}
          tt={progressView.tt}
        />
      </LivingDepthSection>
    </div>
  );
}

import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
import { describeRouteDayShape } from "../../shared/journey/route-day-shape";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { ActivityHistorySection } from "./ActivityHistorySection";
import { ActivityOverviewSection } from "./ActivityOverviewSection";
import { ActivitySignalsSection } from "./ActivitySignalsSection";
import { ActivityStudyLoopSection } from "./ActivityStudyLoopSection";
import { useActivityScreen } from "./useActivityScreen";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";
import { LizaExplainActions } from "../../widgets/liza/LizaExplainActions";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LizaGuidanceGrid } from "../../widgets/liza/LizaGuidanceGrid";
import { RouteIntelligencePanel } from "../../widgets/journey/RouteIntelligencePanel";

export function ActivityScreen() {
  const activityView = useActivityScreen();

  if (!activityView.progress) {
    return <Card>{activityView.tr("Подгружаю activity...")}</Card>;
  }

  const currentFocusArea =
    activityView.dashboard?.journeyState?.currentFocusArea ??
    activityView.dashboard?.dailyLoopPlan?.focusArea ??
    activityView.studyLoop?.focusArea ??
    "activity";
  const journeyState = activityView.dashboard?.journeyState ?? null;
  const routeRecoveryMemory = journeyState?.strategySnapshot.routeRecoveryMemory ?? null;
  const routeReentryProgress = journeyState?.strategySnapshot.routeReentryProgress ?? null;
  const routeEntryMemory = journeyState?.strategySnapshot.routeEntryMemory ?? null;
  const dayShape =
    activityView.dashboard?.dailyLoopPlan
      ? describeRouteDayShape(
          activityView.dashboard.dailyLoopPlan,
          routeRecoveryMemory,
          routeReentryProgress,
          routeEntryMemory,
          activityView.tr,
        )
      : null;
  const coachMessage =
    activityView.locale === "ru"
      ? activityView.hasAvailableDailyRoute
        ? dayShape
          ? `Здесь я собираю в одну ленту только те сигналы, которые реально поддерживают сегодняшнюю route вокруг фокуса ${currentFocusArea}. Сегодня это ${dayShape.title}, поэтому timeline должна подпитывать именно этот ритм, а не распылять внимание.`
          : `Здесь я собираю в одну ленту все сигналы, которые реально двигают обучение вокруг фокуса ${currentFocusArea}, чтобы сегодняшняя route опиралась на живые данные, а не на общие шаблоны.`
        : `Здесь я собираю в одну ленту все сигналы, которые реально двигают обучение: уроки, speaking, listening, vocabulary recovery и свежие результаты вокруг фокуса ${currentFocusArea}.`
      : activityView.hasAvailableDailyRoute
        ? dayShape
          ? `This is where I gather only the signals that truly support today's route around ${currentFocusArea}. Today is a ${dayShape.title}, so the timeline should feed that rhythm instead of scattering attention.`
          : `This is where I gather the signals that truly move the learning path around ${currentFocusArea}, so today's route grows from live evidence rather than a generic template.`
        : `This is where I gather the signals that truly move the learning path: lessons, speaking, listening, vocabulary recovery, and fresh results around ${currentFocusArea}.`;
  const coachSupportingText =
    (dayShape
      ? `${journeyState?.currentStrategySummary ?? activityView.routePriorityView.summary ?? ""} ${activityView.tr("Day shape")}: ${dayShape.title}. ${dayShape.summary}${dayShape.expansionStageLabel ? ` ${activityView.tr("Expansion stage")}: ${dayShape.expansionStageLabel}.` : ""}${dayShape.expansionWindowLabel ? ` ${dayShape.expansionWindowLabel}.` : ""}`.trim()
      : null) ??
    activityView.dashboard?.journeyState?.currentStrategySummary ??
    activityView.routePriorityView.summary ??
    (activityView.locale === "ru"
      ? "Activity должен показывать не просто историю, а причинно-следственную цепочку: что произошло, что это изменило и куда система ведёт дальше."
      : "Activity should show more than history. It should show cause and effect: what happened, what changed, and where the system leads next.");
  const nextActivityStep =
    activityView.dashboard?.journeyState?.nextBestAction ??
    activityView.routePriorityView.summary ??
    (activityView.hasAvailableDailyRoute
      ? dayShape
        ? activityView.locale === "ru"
          ? `Сверь свежие сигналы и вернись в сегодняшнюю route: это ${dayShape.title}${dayShape.expansionStageLabel ? `, этап ${dayShape.expansionStageLabel.toLowerCase()}` : ""}, поэтому после activity важно снова подхватить ${dayShape.sequenceLabel ?? "основной следующий шаг"}.`
          : `Review the fresh signals and return to today's route. This is a ${dayShape.title}${dayShape.expansionStageLabel ? ` in the ${dayShape.expansionStageLabel.toLowerCase()} phase` : ""}, so after activity the right move is to pick up ${dayShape.sequenceLabel ?? "the main next step"} again.`
        : activityView.locale === "ru"
          ? "Сверь свежие сигналы и вернись в сегодняшнюю route: именно она должна собрать activity в один связный следующий шаг."
          : "Review the fresh signals and return to today's route. That route should turn activity into one connected next step."
      : activityView.locale === "ru"
        ? "Посмотри свежие сигналы, затем запусти recovery или вернись в daily loop, чтобы не терять связность маршрута."
        : "Review the fresh signals, then launch recovery or return to the daily loop so the route stays connected.");
  const explainActions = [
    {
      id: "activity-simpler",
      label: activityView.locale === "ru" ? "Объясни проще" : "Explain simpler",
      text:
        activityView.locale === "ru"
          ? "Здесь видно, что именно уже произошло в обучении и какие из этих событий реально влияют на следующий шаг."
          : "This screen shows what has already happened in learning and which of those events truly affect the next step.",
    },
    {
      id: "activity-why",
      label: activityView.locale === "ru" ? "Почему это важно" : "Why it matters",
      text: coachSupportingText,
    },
    {
      id: "activity-priority",
      label: activityView.locale === "ru" ? "Что важнее всего" : "What matters most",
      text:
        activityView.hasAvailableDailyRoute
          ? activityView.locale === "ru"
            ? `Сейчас важнее всего не количество событий, а то, как они подпитывают сегодняшнюю route вокруг ${currentFocusArea}${dayShape?.expansionStageLabel ? ` на этапе ${dayShape.expansionStageLabel.toLowerCase()}` : ""}.`
            : `What matters most right now is not the number of events, but how they feed today's route around ${currentFocusArea}${dayShape?.expansionStageLabel ? ` during the ${dayShape.expansionStageLabel.toLowerCase()} phase` : ""}.`
          : activityView.locale === "ru"
            ? `Сейчас важнее всего не количество событий, а то, как они складываются в один loop вокруг ${currentFocusArea}.`
            : `What matters most right now is not the number of events, but how they combine into one loop around ${currentFocusArea}.`,
    },
    {
      id: "activity-next",
      label: activityView.locale === "ru" ? "Следующий лучший шаг" : "Next best step",
      text: nextActivityStep,
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={activityView.tr("Activity")}
        title={activityView.tr("Unified Activity And History")}
        description={activityView.tr("One timeline for lessons, speaking practice, listening signals, and result history.")}
      />

      <LivingDepthSection id={livingDepthSectionIds.activityCoach}>
        <LizaCoachPanel
          locale={activityView.locale}
          playKey={`activity:${currentFocusArea}:${activityView.recentEvents.length}:${activityView.progress.id}`}
          title={activityView.tr("Liza Activity Layer")}
          message={coachMessage}
          spokenMessage={coachMessage}
          spokenLanguage={activityView.locale}
          replayCta={activityView.tr("Послушать ещё раз")}
          primaryAction={(
            <Button type="button" onClick={() => void activityView.handleStartPrimaryRoute()} className="proof-lesson-primary-button">
              {activityView.primaryRouteLabel}
            </Button>
          )}
          secondaryAction={(
            <Link to={routes.dailyLoop} className="proof-lesson-secondary-action">
              {activityView.hasAvailableDailyRoute
                ? activityView.tr("Открыть route details")
                : activityView.tr("Вернуться в daily loop")}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      <LizaGuidanceGrid
        currentLabel={activityView.locale === "ru" ? "Что сейчас происходит" : "What is happening now"}
        currentText={
          activityView.locale === "ru"
            ? dayShape
              ? `Этот экран собирает unified timeline из lesson history, speaking attempts, listening/pronunciation signals и последнего результата. Сегодня маршрут идёт как ${dayShape.title}, поэтому timeline подчёркивает только те сигналы, которые поддерживают этот ритм.`
              : "Этот экран собирает unified timeline из lesson history, speaking attempts, listening/pronunciation signals и последнего результата."
            : dayShape
              ? `This screen builds a unified timeline from lesson history, speaking attempts, listening/pronunciation signals, and the latest result. Today's route is a ${dayShape.title}, so the timeline highlights only the signals that support that rhythm.`
              : "This screen builds a unified timeline from lesson history, speaking attempts, listening/pronunciation signals, and the latest result."
        }
        whyLabel={activityView.locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          activityView.locale === "ru"
            ? dayShape
              ? `Именно здесь видно, как разные действия складываются в один learning loop вокруг ${currentFocusArea} и подчиняются ритму ${dayShape.title}, а не живут независимыми модулями.`
              : `Именно здесь видно, как разные действия складываются в один learning loop вокруг ${currentFocusArea}, а не живут разными независимыми модулями.`
            : dayShape
              ? `This is where you can see how different actions fold into one learning loop around ${currentFocusArea} and obey the rhythm of ${dayShape.title} rather than living as disconnected modules.`
              : `This is where you can see how different actions fold into one learning loop around ${currentFocusArea} rather than living as disconnected modules.`
        }
        nextLabel={activityView.locale === "ru" ? "Что делать дальше" : "What to do next"}
        nextText={nextActivityStep}
      />

      <LizaExplainActions
        title={activityView.locale === "ru" ? "Разобрать activity с Лизой" : "Break down activity with Liza"}
        actions={explainActions}
      />

      <LivingDepthSection id={livingDepthSectionIds.activityOverview}>
        <ActivityOverviewSection
          lastLessonResult={activityView.lastLessonResult}
          mistakesCount={activityView.mistakes.length}
          progress={activityView.progress}
          pronunciationTrend={activityView.pronunciationTrend}
          speakingAttemptsCount={activityView.speakingAttempts.length}
          tr={activityView.tr}
        />
      </LivingDepthSection>

      <RouteIntelligencePanel
        dailyLoopPlan={activityView.dashboard?.dailyLoopPlan ?? null}
        journeyState={activityView.dashboard?.journeyState ?? null}
        title={activityView.tr("Route intelligence")}
        tr={activityView.tr}
      />

      <LivingDepthSection id={livingDepthSectionIds.activityLoop}>
        <ActivityStudyLoopSection
          expansionStageLabel={dayShape?.expansionStageLabel ?? null}
          hasAvailableDailyRoute={activityView.hasAvailableDailyRoute}
          onStartPrimaryRoute={activityView.handleStartPrimaryRoute}
          onReviewVocabulary={activityView.handleVocabularyReview}
          onStartRecoveryLesson={activityView.handleStartRecoveryLesson}
          primaryRouteLabel={activityView.primaryRouteLabel}
          reviewingVocabularyId={activityView.reviewingVocabularyId}
          studyLoop={activityView.studyLoop}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.activitySignals}>
        <ActivitySignalsSection
          formatDays={activityView.formatDays}
          listeningTrend={activityView.listeningTrend}
          studyLoop={activityView.studyLoop}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>

      <LivingDepthSection id={livingDepthSectionIds.activityHistory}>
        <ActivityHistorySection
          activityError={activityView.activityError}
          events={activityView.recentEvents}
          formatDateTime={activityView.formatDateTime}
          topMistakes={activityView.topMistakes}
          tr={activityView.tr}
          tt={activityView.tt}
        />
      </LivingDepthSection>
    </div>
  );
}

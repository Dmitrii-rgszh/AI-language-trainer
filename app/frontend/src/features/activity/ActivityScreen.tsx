import { Link } from "react-router-dom";
import { routes } from "../../shared/constants/routes";
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
  const coachMessage =
    activityView.locale === "ru"
      ? activityView.hasAvailableDailyRoute
        ? `Здесь я собираю в одну ленту все сигналы, которые реально двигают обучение вокруг фокуса ${currentFocusArea}, чтобы сегодняшняя route опиралась на живые данные, а не на общие шаблоны.`
        : `Здесь я собираю в одну ленту все сигналы, которые реально двигают обучение: уроки, speaking, listening, vocabulary recovery и свежие результаты вокруг фокуса ${currentFocusArea}.`
      : activityView.hasAvailableDailyRoute
        ? `This is where I gather the signals that truly move the learning path around ${currentFocusArea}, so today's route grows from live evidence rather than a generic template.`
        : `This is where I gather the signals that truly move the learning path: lessons, speaking, listening, vocabulary recovery, and fresh results around ${currentFocusArea}.`;
  const coachSupportingText =
    activityView.dashboard?.journeyState?.currentStrategySummary ??
    (activityView.locale === "ru"
      ? "Activity должен показывать не просто историю, а причинно-следственную цепочку: что произошло, что это изменило и куда система ведёт дальше."
      : "Activity should show more than history. It should show cause and effect: what happened, what changed, and where the system leads next.");
  const nextActivityStep =
    activityView.dashboard?.journeyState?.nextBestAction ??
    (activityView.hasAvailableDailyRoute
      ? activityView.locale === "ru"
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
            ? `Сейчас важнее всего не количество событий, а то, как они подпитывают сегодняшнюю route вокруг ${currentFocusArea}.`
            : `What matters most right now is not the number of events, but how they feed today's route around ${currentFocusArea}.`
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
            ? "Этот экран собирает unified timeline из lesson history, speaking attempts, listening/pronunciation signals и последнего результата."
            : "This screen builds a unified timeline from lesson history, speaking attempts, listening/pronunciation signals, and the latest result."
        }
        whyLabel={activityView.locale === "ru" ? "Почему это важно тебе" : "Why it matters for you"}
        whyText={
          activityView.locale === "ru"
            ? `Именно здесь видно, как разные действия складываются в один learning loop вокруг ${currentFocusArea}, а не живут разными независимыми модулями.`
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
          onReviewVocabulary={activityView.handleVocabularyReview}
          onStartRecoveryLesson={activityView.handleStartRecoveryLesson}
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

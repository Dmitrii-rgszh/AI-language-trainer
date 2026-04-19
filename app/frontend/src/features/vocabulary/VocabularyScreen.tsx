import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiClient } from "../../shared/api/client";
import { routes } from "../../shared/constants/routes";
import { useLocale } from "../../shared/i18n/useLocale";
import { resolveRouteFollowUpTransition } from "../../shared/journey/route-follow-up-navigation";
import { buildScreenRouteGovernanceView } from "../../shared/journey/route-priority";
import type { VocabularyHub } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";
import { RouteMicroflowGuard } from "../../widgets/journey/RouteMicroflowGuard";
import { RouteGovernanceNotice } from "../../widgets/journey/RouteGovernanceNotice";
import { LizaCoachPanel } from "../../widgets/liza/LizaCoachPanel";
import { LivingDepthSection } from "../../widgets/living-background/LivingDepthSection";
import { livingDepthSectionIds } from "../../widgets/living-background/livingBackgroundConfig";

export function VocabularyScreen() {
  const { locale, tr, tt } = useLocale();
  const bootstrap = useAppStore((state) => state.bootstrap);
  const dashboard = useAppStore((state) => state.dashboard);
  const navigate = useNavigate();
  const [hub, setHub] = useState<VocabularyHub | null>(null);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [reviewingId, setReviewingId] = useState<string | null>(null);

  async function loadHub() {
    try {
      const nextHub = await apiClient.getVocabularyHub();
      setHub(nextHub);
      setLoadingError(null);
    } catch (error) {
      setLoadingError(error instanceof Error ? error.message : tr("Failed to load vocabulary hub"));
    }
  }

  useEffect(() => {
    void loadHub();
  }, []);

  const handleReview = async (itemId: string, successful: boolean) => {
    setReviewingId(itemId);
    try {
      await apiClient.reviewVocabularyItem(itemId, successful);
      const updatedState = await apiClient.completeRouteReentrySupportStep({ route: routes.vocabulary });
      await Promise.all([loadHub(), bootstrap()]);
      const transition = resolveRouteFollowUpTransition(updatedState, routes.vocabulary, tr);
      if (transition) {
        navigate(transition.route, {
          state: {
            routeEntryReason: transition.reason,
            routeEntrySource: "support_step_follow_up",
            routeEntryFollowUpLabel: transition.nextLabel ?? null,
            routeEntryStageLabel: transition.stageLabel ?? null,
          },
        });
      }
    } finally {
      setReviewingId(null);
    }
  };

  const replayCta = locale === "ru" ? "Послушать ещё раз" : "Hear it again";
  const coachTitle = locale === "ru" ? "Liza Vocabulary Layer" : "Liza Vocabulary Layer";
  const dueCount = hub?.summary.dueCount ?? 0;
  const weakestCategory = hub?.summary.weakestCategory ? tt(hub.summary.weakestCategory) : null;
  const firstDueWord = hub?.dueItems[0]?.word ?? null;
  const routeGovernance = buildScreenRouteGovernanceView(dashboard ?? null, routes.vocabulary, tr);
  const coachMessage =
    locale === "ru"
      ? dueCount > 0
        ? `Словарь сейчас лучше тренировать не случайными списками, а через живую память. У тебя уже ${dueCount} слов в due-очереди${firstDueWord ? `, и я бы начала со слова ${firstDueWord}` : ""}, потому что именно так vocabulary начинает работать в речи и письме.`
        : "Словарь здесь должен жить не как список слов, а как живая память фраз, ошибок и выражений, которые реально возвращаются в твою речь."
      : dueCount > 0
        ? `Vocabulary works better through live memory than random lists. You already have ${dueCount} due items${firstDueWord ? `, and I would begin with ${firstDueWord}` : ""} so the words start working in speaking and writing.`
        : "Vocabulary here should not feel like a static word list. It should become a living memory of phrases, mistakes, and expressions that return to your real language.";
  const coachSpokenMessage =
    locale === "ru"
      ? dueCount > 0
        ? `Сейчас словарь лучше закрепить через due-очередь. Давай возьмём ${firstDueWord ?? "первое слово"} и сразу вернём его в живой контекст.`
        : "Я помогу превратить словарь в живую систему памяти, а не в набор случайных слов."
      : dueCount > 0
        ? `The best vocabulary move right now is your due queue. Let us take ${firstDueWord ?? "the first word"} and move it back into real context right away.`
        : "I will help turn vocabulary into a living memory system instead of a random list of words.";
  const coachSupportingText =
    routeGovernance.isPriorityReentry
      ? routeGovernance.summary
      : routeGovernance.isDeferred
      ? tr("Vocabulary still matters here, but today it should feed the protected return instead of becoming a separate study branch.")
      : locale === "ru"
      ? weakestCategory
        ? `Сейчас самая нагруженная категория — ${weakestCategory}. Это хороший сигнал для умной vocabulary-стратегии: не расширять всё сразу, а удерживать слабые зоны до реальной автоматизации.`
        : "Лиза здесь должна связывать словарь с ошибками, writing, speaking и повторением, чтобы пользователь чувствовал не review queue, а умную языковую память."
      : weakestCategory
        ? `${weakestCategory} is the most loaded category right now. That is a good signal for a smarter vocabulary strategy: do not expand everything at once, stabilize the weakest zone first.`
        : "Liza should connect vocabulary with mistakes, writing, speaking, and review so the user feels a smart language memory rather than a queue.";

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Vocabulary")}
        title={tr("Vocabulary Hub")}
        description={tr(
          "Лёгкий центр словаря: due queue, недавние ревью, баланс между new/active/mastered и теперь ещё видимый источник каждого item.",
        )}
      />

      <RouteGovernanceNotice governance={routeGovernance} tr={tr} />

      <LivingDepthSection id={livingDepthSectionIds.vocabularyCoach}>
        <LizaCoachPanel
          locale={locale}
          playKey={`vocabulary:${dueCount}:${firstDueWord ?? "none"}:${weakestCategory ?? "balanced"}`}
          title={coachTitle}
          message={coachMessage}
          spokenMessage={coachSpokenMessage}
          spokenLanguage={locale}
          replayCta={replayCta}
          primaryAction={(
            <Link to={routeGovernance.isDeferred ? routeGovernance.primaryRoute : routes.speaking} className="proof-lesson-primary-button">
              {routeGovernance.isDeferred
                ? routeGovernance.primaryLabel
                : locale === "ru"
                  ? "Перенести слова в speaking"
                  : "Move words into speaking"}
            </Link>
          )}
          secondaryAction={(
            <Link to={routeGovernance.isDeferred ? routeGovernance.secondaryRoute : routes.writing} className="proof-lesson-secondary-action">
              {routeGovernance.isDeferred
                ? routeGovernance.secondaryLabel
                : locale === "ru"
                  ? "Использовать в writing"
                  : "Use them in writing"}
            </Link>
          )}
          supportingText={coachSupportingText}
        />
      </LivingDepthSection>

      {loadingError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{loadingError}</div>
      ) : null}

      {!hub ? (
        <Card>{tr("Подгружаю vocabulary hub...")}</Card>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Due now")}</div>
              <div className="text-3xl font-semibold text-ink">{hub.summary.dueCount}</div>
            </Card>
            <Card className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("New")}</div>
              <div className="text-3xl font-semibold text-ink">{hub.summary.newCount}</div>
            </Card>
            <Card className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Active")}</div>
              <div className="text-3xl font-semibold text-ink">{hub.summary.activeCount}</div>
            </Card>
            <Card className="space-y-3">
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-coral">{tr("Mastered")}</div>
              <div className="text-3xl font-semibold text-ink">{hub.summary.masteredCount}</div>
              <div className="text-sm text-slate-600">
                {hub.summary.weakestCategory
                  ? `${tr("Most loaded category")}: ${tt(hub.summary.weakestCategory)}`
                  : tr("Queue looks balanced")}
              </div>
            </Card>
          </div>

          <Card className="space-y-3">
            <div className="text-lg font-semibold text-ink">{tr("Why these items are here")}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm leading-6 text-slate-700">
              {tr(
                "Vocabulary review now mixes core study words with captured corrections from lessons, speaking and writing. Source labels show where the item came from, and review reason explains why it is back in your queue now.",
              )}
            </div>
            {hub.mistakeBacklinks.length > 0 ? (
              <div className="space-y-3">
                {hub.mistakeBacklinks.slice(0, 3).map((link) => (
                  <div key={link.weakSpotTitle} className="rounded-2xl bg-mint/30 p-4 text-sm text-slate-700">
                    <div className="font-semibold text-ink">{link.weakSpotTitle}</div>
                    <div className="mt-2">
                      {link.dueCount} {tr("due")}, {link.activeCount} {tr("active")}. Examples: {link.exampleWords.join(", ")}.
                    </div>
                    <div className="mt-2 text-xs uppercase tracking-[0.12em] text-slate-500">
                      {tr("sources")}: {link.sourceModules.map((item) => tt(item)).join(", ")}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </Card>

          <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
            <Card className="space-y-3">
              <div className="text-lg font-semibold text-ink">{tr("Due vocabulary queue")}</div>
              {routeGovernance.isDeferred ? (
                <RouteMicroflowGuard
                  tr={tr}
                  label={routeGovernance.badgeLabel}
                  dayShapeTitle={routeGovernance.dayShapeTitle}
                  dayShapeCompactnessLabel={routeGovernance.dayShapeCompactnessLabel}
                  dayShapeSummary={routeGovernance.dayShapeSummary}
                  dayShapeExpansionStageLabel={routeGovernance.dayShapeExpansionStageLabel}
                  dayShapeExpansionWindowLabel={routeGovernance.dayShapeExpansionWindowLabel}
                  message={
                    routeGovernance.state === "sequenced_hold"
                      ? tr("Vocabulary review will reopen later in the re-entry sequence, after the focused support surface has been used first.")
                      : tr("Vocabulary review stays visible, but active marking should wait until today's protected return is complete.")
                  }
                />
              ) : null}
              {hub.dueItems.length === 0 ? (
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("No due items right now.")}</div>
              ) : (
                hub.dueItems.map((item) => (
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
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full bg-mint/40 px-3 py-1 font-semibold uppercase tracking-[0.12em] text-slate-700">
                        {tr("source")}: {tt(item.sourceModule)}
                      </span>
                      <span className="rounded-full bg-sand px-3 py-1 text-slate-700">{tt(item.category)}</span>
                    </div>
                    <div className="mt-3 rounded-2xl bg-mint/30 p-3 text-sm text-slate-700">{item.reviewReason}</div>
                    <div className="mt-4 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => void handleReview(item.id, true)}
                        disabled={routeGovernance.isMicroflowLocked || reviewingId === item.id}
                        className="rounded-full bg-ink px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-ink/85 disabled:opacity-60"
                      >
                        {reviewingId === item.id ? tr("Saving...") : tr("Mark correct")}
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleReview(item.id, false)}
                        disabled={routeGovernance.isMicroflowLocked || reviewingId === item.id}
                        className="rounded-full bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink transition hover:bg-[#ddccb6] disabled:opacity-60"
                      >
                        {tr("Need review")}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </Card>

            <Card className="space-y-3">
              <div className="text-lg font-semibold text-ink">{tr("Recently reviewed")}</div>
              {hub.recentItems.length === 0 ? (
                <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">{tr("Recent vocabulary activity will appear here.")}</div>
              ) : (
                hub.recentItems.map((item) => (
                  <div key={item.id} className="rounded-2xl bg-white/70 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-ink">{item.word}</div>
                        <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.learnedStatus)}</div>
                      </div>
                      <div className="text-sm text-slate-600">{tr("stage")} {item.repetitionStage}</div>
                    </div>
                    <div className="mt-3 text-sm text-slate-600">{item.context}</div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-full bg-mint/40 px-3 py-1 font-semibold uppercase tracking-[0.12em] text-slate-700">
                        {tr("source")}: {tt(item.sourceModule)}
                      </span>
                      <span className="rounded-full bg-sand px-3 py-1 text-slate-700">{tt(item.category)}</span>
                    </div>
                    <div className="mt-3 rounded-2xl bg-mint/30 p-3 text-sm text-slate-700">{item.reviewReason}</div>
                  </div>
                ))
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

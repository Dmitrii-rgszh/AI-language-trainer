import { useEffect, useState } from "react";
import { apiClient } from "../../shared/api/client";
import { useLocale } from "../../shared/i18n/useLocale";
import type { VocabularyHub } from "../../shared/types/app-data";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function VocabularyScreen() {
  const { tr, tt } = useLocale();
  const bootstrap = useAppStore((state) => state.bootstrap);
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
      await Promise.all([loadHub(), bootstrap()]);
    } finally {
      setReviewingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Vocabulary")}
        title={tr("Vocabulary Hub")}
        description={tr(
          "Лёгкий центр словаря: due queue, недавние ревью, баланс между new/active/mastered и теперь ещё видимый источник каждого item.",
        )}
      />

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
                        disabled={reviewingId === item.id}
                        className="rounded-full bg-ink px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white transition hover:bg-ink/85 disabled:opacity-60"
                      >
                        {reviewingId === item.id ? tr("Saving...") : tr("Mark correct")}
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleReview(item.id, false)}
                        disabled={reviewingId === item.id}
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

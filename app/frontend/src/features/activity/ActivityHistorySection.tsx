import { Link } from "react-router-dom";
import type { Mistake } from "../../entities/mistake/model";
import { routes } from "../../shared/constants/routes";
import { Card } from "../../shared/ui/Card";
import type { ActivityEvent } from "./useActivityScreen";

type ActivityHistorySectionProps = {
  activityError: string | null;
  events: ActivityEvent[];
  formatDateTime: (value: string) => string;
  topMistakes: Mistake[];
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ActivityHistorySection({
  activityError,
  events,
  formatDateTime,
  topMistakes,
  tr,
  tt,
}: ActivityHistorySectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Recent timeline")}</div>
          <div className="flex flex-wrap gap-2">
            <Link
              to={routes.progress}
              className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink"
            >
              {tr("Lessons")}
            </Link>
            <Link
              to={routes.speaking}
              className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink"
            >
              {tr("Speaking")}
            </Link>
            <Link
              to={routes.pronunciation}
              className="rounded-2xl bg-sand px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-ink"
            >
              {tr("Pronunciation")}
            </Link>
          </div>
        </div>
        {activityError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {activityError}
          </div>
        ) : null}
        {events.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Activity feed will populate after the first lesson completion or speaking attempt.")}
          </div>
        ) : (
          events.map((event) => (
            <Link key={event.id} to={event.route} className="block rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(event.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(event.meta)}</div>
                </div>
                <div className="text-xs text-slate-500">
                  {event.createdAt ? formatDateTime(event.createdAt) : tr("current session")}
                </div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{tr(event.detail)}</div>
            </Link>
          ))
        )}
      </Card>

      <div className="space-y-4">
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Top mistake patterns")}</div>
            <Link to={routes.mistakes} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open all")}
            </Link>
          </div>
          {topMistakes.length === 0 ? (
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
              {tr("Mistake analytics will appear here after lesson completion and correction extraction.")}
            </div>
          ) : (
            topMistakes.map((mistake) => (
              <div key={mistake.id} className="rounded-2xl bg-white/70 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-ink">{tr(mistake.subtype)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">
                      {tt(mistake.category)} • {tt(mistake.sourceModule)}
                    </div>
                  </div>
                  <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                    {tr("repeats")} {mistake.repetitionCount}
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-600">{tr(mistake.explanation)}</div>
              </div>
            ))
          )}
        </Card>

        <Card className="space-y-3">
          <div className="text-lg font-semibold text-ink">{tr("Quick jumps")}</div>
          <Link to={routes.lessonResults} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Current lesson result")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("Open the latest in-session result screen if a recent completion happened.")}
            </div>
          </Link>
          <Link to={routes.progress} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Progress deep dive")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("See skill balances, daily goal and recent lesson history.")}
            </div>
          </Link>
          <Link to={routes.speaking} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Speaking practice log")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("Continue voice training and review speaking attempts in detail.")}
            </div>
          </Link>
          <Link to={routes.pronunciation} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Pronunciation trend view")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("Review recurring weak sounds and pronunciation history outside the lab context.")}
            </div>
          </Link>
          <Link to={routes.vocabulary} className="block rounded-2xl bg-white/70 p-4">
            <div className="text-sm font-semibold text-ink">{tr("Vocabulary hub")}</div>
            <div className="mt-2 text-sm text-slate-600">
              {tr("Review due cards, recent vocabulary activity and queue balance.")}
            </div>
          </Link>
        </Card>
      </div>
    </div>
  );
}

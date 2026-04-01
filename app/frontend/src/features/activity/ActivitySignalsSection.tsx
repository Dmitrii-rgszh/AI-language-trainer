import { Link } from "react-router-dom";
import type { AdaptiveStudyLoop, ListeningTrend } from "../../shared/types/app-data";
import { resolutionTone } from "../../shared/activity/resolution-tone";
import { routes } from "../../shared/constants/routes";
import { Card } from "../../shared/ui/Card";

type ActivitySignalsSectionProps = {
  formatDays: (value: number) => string;
  listeningTrend: ListeningTrend | null;
  studyLoop: AdaptiveStudyLoop | null;
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function ActivitySignalsSection({
  formatDays,
  listeningTrend,
  studyLoop,
  tr,
  tt,
}: ActivitySignalsSectionProps) {
  return (
    <>
      {studyLoop?.vocabularyBacklinks.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Mistake to vocabulary loop")}</div>
            <Link to={routes.vocabulary} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open hub")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {studyLoop.vocabularyBacklinks.map((link) => (
              <div key={link.weakSpotTitle} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-ink">{tr(link.weakSpotTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(link.weakSpotCategory)}</div>
                  </div>
                  <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">
                    {link.dueCount} {tr("due")} / {link.activeCount} {tr("active")}
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-600">
                  {tr("Converted examples")}: {link.exampleWords.join(", ")}.
                </div>
                <div className="mt-2 text-xs uppercase tracking-[0.12em] text-slate-500">
                  {tr("sources")}: {link.sourceModules.map((item) => tt(item)).join(", ")}
                </div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {studyLoop?.mistakeResolution.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Weak spot recovery visibility")}</div>
            <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open progress")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {studyLoop.mistakeResolution.map((item) => (
              <div key={item.weakSpotTitle} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-ink">{tr(item.weakSpotTitle)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(item.weakSpotCategory)}</div>
                  </div>
                  <div
                    className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${resolutionTone(item.status)}`}
                  >
                    {tr(item.status)}
                  </div>
                </div>
                <div className="mt-3 text-sm text-slate-600">
                  {tr("Repeats")}: {item.repetitionCount}. {tr("Last seen")} {formatDays(item.lastSeenDaysAgo)} ago.{" "}
                  {tr("Linked vocabulary")}: {item.linkedVocabularyCount}.
                </div>
                <div className="mt-3 rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">{tr(item.resolutionHint)}</div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {studyLoop?.moduleRotation.length ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Module rotation balance")}</div>
            <Link to={routes.dashboard} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open dashboard")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {studyLoop.moduleRotation.slice(0, 3).map((item) => (
              <Link key={item.moduleKey} to={item.route} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
                <div className="text-xs uppercase tracking-[0.16em] text-coral">
                  {tr("priority")} {item.priority}
                </div>
                <div className="mt-2 font-semibold text-ink">{tr(item.title)}</div>
                <div className="mt-3 text-slate-600">{tr(item.reason)}</div>
              </Link>
            ))}
          </div>
        </Card>
      ) : null}

      {listeningTrend ? (
        <Card className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="text-lg font-semibold text-ink">{tr("Listening contribution")}</div>
            <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
              {tr("Open progress")}
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Average score")}: <span className="font-semibold text-ink">{listeningTrend.averageScore}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Recent attempts")}: <span className="font-semibold text-ink">{listeningTrend.recentAttempts}</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {tr("Transcript support")}:{" "}
              <span className="font-semibold text-ink">{listeningTrend.transcriptSupportRate}%</span>
            </div>
          </div>
        </Card>
      ) : null}
    </>
  );
}

import { Link } from "react-router-dom";
import type { ProviderStatus } from "../../shared/types/app-data";
import { routes } from "../../shared/constants/routes";
import { Card } from "../../shared/ui/Card";
import type { DashboardActivityEvent } from "./useDashboardScreen";

type DashboardRecentActivitySectionProps = {
  activityError: string | null;
  events: DashboardActivityEvent[];
  formatDateTime: (value: string) => string;
  providers: ProviderStatus[];
  tr: (value: string) => string;
  tt: (value: string) => string;
};

export function DashboardRecentActivitySection({
  activityError,
  events,
  formatDateTime,
  providers,
  tr,
  tt,
}: DashboardRecentActivitySectionProps) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Recent activity")}</div>
          <Link to={routes.progress} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
            {tr("Open progress")}
          </Link>
        </div>
        {activityError ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {activityError}
          </div>
        ) : null}
        {events.length === 0 ? (
          <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-600">
            {tr("Activity will appear here after the first completed lesson or speaking attempt.")}
          </div>
        ) : (
          events.map((event) => (
            <Link key={event.id} to={event.route} className="block rounded-2xl bg-white/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-ink">{tr(event.title)}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tr(event.meta)}</div>
                </div>
                <div className="text-xs text-slate-500">{formatDateTime(event.createdAt)}</div>
              </div>
              <div className="mt-3 text-sm text-slate-600">{tr(event.detail)}</div>
            </Link>
          ))
        )}
      </Card>

      <Card className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="text-lg font-semibold text-ink">{tr("Provider health")}</div>
          <Link to={routes.settings} className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">
            {tr("Open settings")}
          </Link>
        </div>
        {providers.map((provider) => (
          <div key={provider.key} className="rounded-2xl bg-white/70 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-ink">{provider.name}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-coral">{tt(provider.type)}</div>
              </div>
              <div className="rounded-2xl bg-sand px-3 py-2 text-xs text-slate-700">{tr(provider.status)}</div>
            </div>
            <div className="mt-3 text-sm text-slate-600">{tr(provider.details)}</div>
          </div>
        ))}
      </Card>
    </div>
  );
}

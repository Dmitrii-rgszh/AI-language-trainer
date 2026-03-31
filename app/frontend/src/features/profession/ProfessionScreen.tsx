import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function ProfessionScreen() {
  const { tr, tt, tl } = useLocale();
  const tracks = useAppStore((state) => state.professionTracks);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Professional English")}
        title={tr("Profession Hub")}
        description={tr("Choose the professional track that should shape your vocabulary, scenarios, and lesson emphasis.")}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {tracks.map((track) => (
          <Card key={track.id} className="space-y-4">
            <div>
              <div className="text-lg font-semibold text-ink">{tr(track.title)}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(track.domain)}</div>
            </div>
            <div className="text-sm leading-6 text-slate-700">{tr(track.summary)}</div>
            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {track.lessonFocus.map((focus) => (
                <div key={focus}>• {tl([focus])}</div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

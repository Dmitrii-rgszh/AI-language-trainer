import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function MistakesScreen() {
  const { tr, tt } = useLocale();
  const mistakes = useAppStore((state) => state.mistakes);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Mistake Analytics")}
        title={tr("My Mistakes")}
        description={tr("Review recurring patterns, compare corrections, and see what still needs active recovery.")}
      />

      <div className="space-y-4">
        {mistakes.map((mistake) => (
          <Card key={mistake.id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{tr(mistake.subtype)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{tt(mistake.category)}</div>
              </div>
              <div className="rounded-2xl bg-white/70 px-3 py-2 text-sm text-slate-700">
                {tr("repeats")}: {mistake.repetitionCount}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl bg-[#fff0ea] p-4 text-sm text-slate-700">{mistake.originalText}</div>
              <div className="rounded-2xl bg-[#ecfffb] p-4 text-sm text-slate-700">{mistake.correctedText}</div>
            </div>

            <div className="text-sm leading-6 text-slate-700">{tr(mistake.explanation)}</div>
          </Card>
        ))}
      </div>
    </div>
  );
}

import { useLocale } from "../../shared/i18n/useLocale";
import { useAppStore } from "../../shared/store/app-store";
import { Card } from "../../shared/ui/Card";
import { ProgressBar } from "../../shared/ui/ProgressBar";
import { SectionHeading } from "../../shared/ui/SectionHeading";

export function GrammarScreen() {
  const { tr } = useLocale();
  const grammarTopics = useAppStore((state) => state.grammarTopics);

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow={tr("Grammar Coach")}
        title={tr("Grammar Center")}
        description={tr(
          "MVP-модуль хранит темы отдельно от UI и уже показывает mastery, explanation и checkpoints для дальнейшего расширения упражнениями.",
        )}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        {grammarTopics.map((topic) => (
          <Card key={topic.id} className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-semibold text-ink">{tr(topic.title)}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.18em] text-coral">{topic.level}</div>
              </div>
              <div className="rounded-2xl bg-white/70 px-3 py-2 text-sm font-semibold text-ink">
                {topic.mastery}%
              </div>
            </div>

            <ProgressBar value={topic.mastery} />
            <div className="text-sm leading-6 text-slate-700">{tr(topic.explanation)}</div>

            <div className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              {topic.checkpoints.map((checkpoint) => (
                <div key={checkpoint}>• {tr(checkpoint)}</div>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

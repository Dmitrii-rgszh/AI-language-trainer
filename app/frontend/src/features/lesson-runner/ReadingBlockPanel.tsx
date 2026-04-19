type ReadingBlockPanelProps = {
  readingPassage: string;
  readingQuestions: string[];
  readingTitle?: string | null;
  tr: (value: string) => string;
};

export function ReadingBlockPanel({
  readingPassage,
  readingQuestions,
  readingTitle,
  tr,
}: ReadingBlockPanelProps) {
  return (
    <div className="space-y-3 rounded-2xl border border-coral/15 bg-coral/6 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-ink">{readingTitle ?? tr("Reading support")}</div>
        <div className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-coral">
          {tr("Read before answering")}
        </div>
      </div>
      <div className="rounded-2xl bg-white/82 p-4 text-sm leading-6 text-slate-700">{readingPassage}</div>
      {readingQuestions.length > 0 ? (
        <div className="rounded-2xl bg-white/82 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{tr("Key questions")}</div>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-700">
            {readingQuestions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

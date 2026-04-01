type LessonRunnerResponseFieldProps = {
  onChange: (value: string) => void;
  tr: (value: string) => string;
  value: string;
};

export function LessonRunnerResponseField({ onChange, tr, value }: LessonRunnerResponseFieldProps) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold text-ink">{tr("Your response")}</div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={tr("Напиши или вставь свой ответ по этому блоку. Он сохранится в lesson run и может попасть в mistakes analytics.")}
        className="min-h-[140px] w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm text-slate-700 outline-none"
      />
    </div>
  );
}

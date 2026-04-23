type LessonRunnerResponseFieldProps = {
  compact?: boolean;
  label?: string;
  multiline?: boolean;
  onChange: (value: string) => void;
  placeholder?: string;
  tr: (value: string) => string;
  value: string;
};

export function LessonRunnerResponseField({
  compact = false,
  label,
  multiline = true,
  onChange,
  placeholder,
  tr,
  value,
}: LessonRunnerResponseFieldProps) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-semibold text-ink">{label ?? tr("Your response")}</div>
      {multiline ? (
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={
            placeholder ??
            tr("Напиши или вставь свой ответ по этому блоку. Он сохранится в lesson run и может попасть в mistakes analytics.")
          }
          className={`w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm text-slate-700 outline-none ${
            compact ? "min-h-[104px]" : "min-h-[140px]"
          }`}
        />
      ) : (
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder ?? tr("Write your answer")}
          className="w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm text-slate-700 outline-none"
        />
      )}
    </div>
  );
}

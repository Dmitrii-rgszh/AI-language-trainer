interface ScoreBadgeProps {
  label: string;
  score: number;
}

export function ScoreBadge({ label, score }: ScoreBadgeProps) {
  return (
    <div className="rounded-2xl bg-white/70 px-3 py-2">
      <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-ink">{score}%</div>
    </div>
  );
}


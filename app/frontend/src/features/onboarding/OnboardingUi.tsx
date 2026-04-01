import { cn } from "../../shared/utils/cn";

type StepRailButtonProps = {
  active: boolean;
  completed: boolean;
  index: number;
  onClick: () => void;
  title: string;
  unlocked: boolean;
};

export function StepRailButton({
  active,
  completed,
  index,
  onClick,
  title,
  unlocked,
}: StepRailButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!unlocked}
      className={cn(
        "flex w-full items-center gap-3 rounded-[24px] border px-4 py-3 text-left transition-all",
        active
          ? "border-accent/50 bg-white text-ink shadow-soft"
          : "border-white/50 bg-white/50 text-slate-700 hover:bg-white",
        !unlocked && "cursor-not-allowed opacity-60 hover:bg-white/50",
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
          active
            ? "bg-accent text-white"
            : completed
              ? "bg-teal-100 text-teal-800"
              : "bg-sand/90 text-slate-700",
        )}
      >
        {completed ? "OK" : index + 1}
      </div>
      <div className="text-sm font-semibold">{title}</div>
    </button>
  );
}

type ChoiceCardProps = {
  active: boolean;
  delay?: number;
  onClick: () => void;
  subtitle?: string;
  title: string;
};

export function ChoiceCard({ active, delay = 0, onClick, subtitle, title }: ChoiceCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{ animationDelay: `${delay}ms` }}
      className={cn(
        "onboarding-stagger-item rounded-[26px] border px-4 py-4 text-left transition-all",
        active
          ? "border-accent/50 bg-accent/10 text-ink shadow-soft"
          : "border-white/60 bg-white/70 text-slate-700 hover:-translate-y-0.5 hover:bg-white",
      )}
    >
      <div className="text-sm font-semibold">{title}</div>
      {subtitle ? <div className="mt-2 text-sm leading-6 text-slate-500">{subtitle}</div> : null}
    </button>
  );
}

type MetricSliderProps = {
  delay?: number;
  label: string;
  onChange: (value: number) => void;
  value: number;
};

export function MetricSlider({ delay = 0, label, onChange, value }: MetricSliderProps) {
  return (
    <label
      style={{ animationDelay: `${delay}ms` }}
      className="onboarding-stagger-item block rounded-[24px] border border-white/60 bg-white/70 p-4 text-sm text-slate-700"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="font-semibold text-ink">{label}</span>
        <span className="rounded-full bg-sand px-3 py-1 text-xs font-semibold text-slate-700">{value}/10</span>
      </div>
      <input
        type="range"
        min={1}
        max={10}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="mt-4 w-full accent-[#0f766e]"
      />
    </label>
  );
}

type FieldStatusBadgeProps = {
  badgeClassName: string;
  dotClassName: string;
  text: string;
  textClassName?: string;
};

export function FieldStatusBadge({
  badgeClassName,
  dotClassName,
  text,
  textClassName,
}: FieldStatusBadgeProps) {
  return (
    <div
      aria-live="polite"
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold",
        badgeClassName,
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", dotClassName)} />
      <span className={textClassName}>{text}</span>
    </div>
  );
}

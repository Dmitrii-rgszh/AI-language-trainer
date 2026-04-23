type LessonRunnerStatusBannerProps = {
  completed: boolean;
  score?: number | null;
  tr: (value: string) => string;
};

export function LessonRunnerStatusBanner({ completed, score, tr }: LessonRunnerStatusBannerProps) {
  if (completed) {
    return (
      <div className="rounded-2xl bg-accent px-4 py-4 text-white">
        {tr("Lesson complete. Estimated score")}: {score ?? 78}. {tr("Open the results and move on.")}
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-600">
      {tr("Your progress will stay here if you come back later.")}
    </div>
  );
}

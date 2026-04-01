type LessonRunnerStatusBannerProps = {
  completed: boolean;
  score?: number | null;
  tr: (value: string) => string;
};

export function LessonRunnerStatusBanner({ completed, score, tr }: LessonRunnerStatusBannerProps) {
  if (completed) {
    return (
      <div className="rounded-2xl bg-accent px-4 py-4 text-white">
        {tr("Lesson complete. Estimated score")}: {score ?? 78}.{" "}
        {tr("Results can now be forwarded into progress and mistakes analytics.")}
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white/70 px-4 py-3 text-sm text-slate-600">
      {tr("Draft mode active. Saved block responses will be restored if you leave and reopen this lesson.")}
    </div>
  );
}

import { Button } from "../../shared/ui/Button";
import { Card } from "../../shared/ui/Card";

type LessonRunnerEmptyStateProps = {
  onBuildLesson: () => Promise<void>;
  tr: (value: string) => string;
};

export function LessonRunnerEmptyState({ onBuildLesson, tr }: LessonRunnerEmptyStateProps) {
  return (
    <Card className="space-y-4">
      <div className="text-lg font-semibold text-ink">{tr("No lesson loaded yet")}</div>
      <div className="text-sm text-slate-600">
        {tr("Если незавершённый draft есть в backend, экран автоматически попробует его восстановить.")}
      </div>
      <Button onClick={() => void onBuildLesson()}>{tr("Build recommended lesson")}</Button>
    </Card>
  );
}

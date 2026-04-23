import { Button } from "../../shared/ui/Button";

type LessonRunnerActionBarProps = {
  canGoBack: boolean;
  isLastBlock: boolean;
  onComplete: () => Promise<void>;
  onDiscard: () => Promise<void>;
  onNext: () => Promise<void>;
  onPrevious: () => Promise<void>;
  onRestart: () => Promise<void>;
  onSave: () => Promise<void>;
  tr: (value: string) => string;
};

export function LessonRunnerActionBar({
  canGoBack,
  isLastBlock,
  onComplete,
  onDiscard,
  onNext,
  onPrevious,
  onRestart,
  onSave,
  tr,
}: LessonRunnerActionBarProps) {
  return (
    <div className="space-y-3">
      <div>
        {!isLastBlock ? <Button onClick={() => void onNext()}>{tr("Next")}</Button> : null}
        {isLastBlock ? <Button onClick={() => void onComplete()}>{tr("Finish lesson")}</Button> : null}
      </div>
      <details className="group">
        <summary className="cursor-pointer text-sm font-semibold text-slate-500 transition-colors hover:text-ink">
          {tr("Other actions")}
        </summary>
        <div className="mt-3 flex flex-wrap gap-3">
          <Button variant="ghost" onClick={() => void onPrevious()} disabled={!canGoBack}>
            {tr("Previous")}
          </Button>
          <Button variant="ghost" onClick={() => void onSave()}>
            {tr("Save for later")}
          </Button>
          <Button variant="ghost" onClick={() => void onRestart()}>
            {tr("Start over")}
          </Button>
          <Button variant="ghost" onClick={() => void onDiscard()}>
            {tr("Close lesson")}
          </Button>
        </div>
      </details>
    </div>
  );
}

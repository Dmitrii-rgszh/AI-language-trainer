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
    <div className="flex flex-wrap gap-3">
      <Button variant="ghost" onClick={() => void onPrevious()} disabled={!canGoBack}>
        {tr("Previous")}
      </Button>
      <Button variant="secondary" onClick={() => void onSave()}>
        {tr("Save block")}
      </Button>
      <Button variant="secondary" onClick={() => void onRestart()}>
        {tr("Restart lesson")}
      </Button>
      <Button variant="ghost" onClick={() => void onDiscard()}>
        {tr("Discard draft")}
      </Button>
      {!isLastBlock ? <Button onClick={() => void onNext()}>{tr("Next block")}</Button> : null}
      {isLastBlock ? <Button onClick={() => void onComplete()}>{tr("Complete lesson")}</Button> : null}
    </div>
  );
}

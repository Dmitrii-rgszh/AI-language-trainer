import { Button } from "../../shared/ui/Button";

type PronunciationBlockPanelProps = {
  isAssessingPronunciation: boolean;
  isRecordingPronunciation: boolean;
  onPlayModel: (target: string) => void;
  onToggleRecording: (target: string) => void;
  pronunciationTarget: string | null;
  pronunciationTargets: string[];
  tr: (value: string) => string;
};

export function PronunciationBlockPanel({
  isAssessingPronunciation,
  isRecordingPronunciation,
  onPlayModel,
  onToggleRecording,
  pronunciationTarget,
  pronunciationTargets,
  tr,
}: PronunciationBlockPanelProps) {
  return (
    <div className="space-y-3 rounded-2xl bg-white/70 p-4">
      <div className="text-sm font-semibold text-ink">{tr("Pronunciation checkpoint")}</div>
      {pronunciationTargets.map((target) => (
        <div key={target} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-sand/80 p-3">
          <span className="text-sm text-slate-700">{target}</span>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => onPlayModel(target)}>
              {tr("Play model")}
            </Button>
            <Button onClick={() => onToggleRecording(target)} disabled={isAssessingPronunciation}>
              {isRecordingPronunciation && pronunciationTarget === target
                ? tr("Stop & score")
                : isAssessingPronunciation && pronunciationTarget === target
                  ? tr("Scoring...")
                  : tr("Record response")}
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

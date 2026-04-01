import { Button } from "../../shared/ui/Button";

type ListeningBlockPanelProps = {
  isPlayingListening: boolean;
  listeningQuestions: string[];
  listeningTranscript: string;
  listeningVariants: Array<{ label?: string }>;
  markTranscriptUsed: () => void;
  onPlay: () => void;
  onSwitchVariant: () => void;
  selectedListeningVariantIndex: number;
  selectedListeningVariantLabel?: string;
  showListeningTranscript: boolean;
  toggleTranscript: () => void;
  transcriptWasRevealed: boolean;
  tr: (value: string) => string;
};

export function ListeningBlockPanel({
  isPlayingListening,
  listeningQuestions,
  listeningTranscript,
  listeningVariants,
  markTranscriptUsed,
  onPlay,
  onSwitchVariant,
  selectedListeningVariantIndex,
  selectedListeningVariantLabel,
  showListeningTranscript,
  toggleTranscript,
  transcriptWasRevealed,
  tr,
}: ListeningBlockPanelProps) {
  return (
    <div className="space-y-3 rounded-2xl bg-white/70 p-4">
      <div className="text-sm font-semibold text-ink">{tr("Listening audio")}</div>
      {listeningVariants.length > 1 ? (
        <div className="rounded-2xl bg-sand/80 p-3 text-sm text-slate-700">
          {tr("Active variant")}:{" "}
          <span className="font-semibold text-ink">
            {selectedListeningVariantLabel ?? `${tr("Variant")} ${selectedListeningVariantIndex + 1}`}
          </span>{" "}
          ({selectedListeningVariantIndex + 1}/{listeningVariants.length})
        </div>
      ) : null}
      {listeningQuestions.length > 0 ? (
        <div className="rounded-2xl bg-sand/80 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-coral">{tr("Questions")}</div>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {listeningQuestions.map((question) => (
              <li key={question}>• {question}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-3">
        <Button variant="secondary" onClick={onPlay}>
          {isPlayingListening ? tr("Playing...") : tr("Play audio prompt")}
        </Button>
        {listeningVariants.length > 1 ? (
          <Button variant="secondary" onClick={onSwitchVariant}>
            {tr("Switch audio variant")}
          </Button>
        ) : null}
        <Button
          variant="ghost"
          onClick={() => {
            if (!showListeningTranscript) {
              markTranscriptUsed();
            }
            toggleTranscript();
          }}
        >
          {showListeningTranscript ? tr("Hide transcript") : tr("Reveal transcript")}
        </Button>
      </div>
      {showListeningTranscript ? (
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">{listeningTranscript}</div>
      ) : (
        <div className="rounded-2xl bg-sand/80 p-4 text-sm text-slate-700">
          {tr("Try answering from audio first, then reveal transcript only if needed.")}
        </div>
      )}
      {transcriptWasRevealed ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
          {tr("Transcript support was used for this checkpoint. Listening score will stay slightly more conservative.")}
        </div>
      ) : null}
    </div>
  );
}

import type { LessonBlock } from "../../entities/lesson/model";

export function LessonBlockPayload({ block }: { block: LessonBlock }) {
  return (
    <div className="grid gap-3">
      {Object.entries(block.payload)
        .filter(
          ([key]) =>
            !(
              block.blockType === "listening_block" &&
              ["transcript", "audio_asset_id", "audio_variants", "questions", "answer_key", "answerKey"].includes(key)
            ),
        )
        .map(([key, value]) => {
          if (Array.isArray(value)) {
            return (
              <div key={key} className="rounded-2xl bg-white/70 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{key}</div>
                <ul className="mt-3 space-y-2 text-sm text-slate-700">
                  {value.map((item, index) => (
                    <li key={`${block.id}-${index}`}>• {String(item)}</li>
                  ))}
                </ul>
              </div>
            );
          }

          return (
            <div key={key} className="rounded-2xl bg-white/70 p-4 text-sm text-slate-700">
              <span className="font-semibold text-ink">{key}:</span> {String(value)}
            </div>
          );
        })}
    </div>
  );
}

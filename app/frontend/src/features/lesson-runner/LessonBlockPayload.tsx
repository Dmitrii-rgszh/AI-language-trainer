import type { LessonBlock } from "../../entities/lesson/model";

export function LessonBlockPayload({ block }: { block: LessonBlock }) {
  const routeContext =
    typeof block.payload.routeContext === "object" && block.payload.routeContext !== null
      ? (block.payload.routeContext as {
          focusArea?: string;
          sessionKind?: string;
          routeHeadline?: string;
          whyNow?: string;
          nextBestAction?: string;
          primaryGoal?: string;
          preferredMode?: string;
          routeSeedSource?: string;
          inputLane?: string;
          outputLane?: string;
          moduleRotationKeys?: string[];
          activeSkillFocus?: string[];
          weakSpotTitles?: string[];
          dueVocabularyWords?: string[];
          carryOverSignalLabel?: string;
          watchSignalLabel?: string;
        })
      : null;
  const continuityPayload =
    typeof block.payload.continuity === "object" && block.payload.continuity !== null
      ? (block.payload.continuity as {
          focusArea?: string;
          continuityMode?: string;
          carryOverSignalLabel?: string;
          watchSignalLabel?: string;
          strategyShift?: string;
          sessionHeadline?: string;
          weakSpotTitles?: string[];
          dueVocabularyWords?: string[];
        })
      : null;

  return (
    <div className="grid gap-3">
      {routeContext ? (
        <div className="rounded-2xl border border-coral/20 bg-coral/8 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">route guidance</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {routeContext.routeHeadline ?? `Today's route stays focused on ${routeContext.focusArea ?? "your next signal"}.`}
          </div>
          {routeContext.whyNow ? (
            <div className="mt-3 text-sm leading-6 text-slate-700">{routeContext.whyNow}</div>
          ) : null}
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {routeContext.primaryGoal ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">main goal:</span> {routeContext.primaryGoal}
              </div>
            ) : null}
            {routeContext.preferredMode ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">preferred mode:</span> {routeContext.preferredMode}
              </div>
            ) : null}
            {routeContext.routeSeedSource ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">route seed:</span> {routeContext.routeSeedSource}
              </div>
            ) : null}
            {routeContext.focusArea ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">focus area:</span> {routeContext.focusArea}
              </div>
            ) : null}
            {routeContext.inputLane || routeContext.outputLane ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">route shape:</span>{" "}
                {[routeContext.inputLane, routeContext.outputLane].filter(Boolean).join(" -> ")}
              </div>
            ) : null}
          </div>
          {routeContext.moduleRotationKeys?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">module rotation:</span> {routeContext.moduleRotationKeys.join(", ")}
            </div>
          ) : null}
          {routeContext.activeSkillFocus?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">active skills:</span> {routeContext.activeSkillFocus.join(", ")}
            </div>
          ) : null}
          {routeContext.nextBestAction ? (
            <div className="mt-3 text-sm leading-6 text-slate-700">
              <span className="font-semibold text-ink">next route step:</span> {routeContext.nextBestAction}
            </div>
          ) : null}
        </div>
      ) : null}

      {continuityPayload ? (
        <div className="rounded-2xl border border-accent/20 bg-accent/8 p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">continuity</div>
          <div className="mt-2 text-sm font-semibold text-ink">
            {continuityPayload.sessionHeadline ?? `Route stays focused on ${continuityPayload.focusArea ?? "your next signal"}.`}
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {continuityPayload.carryOverSignalLabel ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">carry forward:</span> {continuityPayload.carryOverSignalLabel}
              </div>
            ) : null}
            {continuityPayload.watchSignalLabel ? (
              <div className="rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
                <span className="font-semibold text-ink">watch next:</span> {continuityPayload.watchSignalLabel}
              </div>
            ) : null}
          </div>
          {continuityPayload.weakSpotTitles?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">weak spots in play:</span> {continuityPayload.weakSpotTitles.join(", ")}
            </div>
          ) : null}
          {continuityPayload.dueVocabularyWords?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">active words:</span> {continuityPayload.dueVocabularyWords.join(", ")}
            </div>
          ) : null}
          {continuityPayload.strategyShift ? (
            <div className="mt-3 text-sm leading-6 text-slate-700">{continuityPayload.strategyShift}</div>
          ) : null}
        </div>
      ) : null}

      {Object.entries(block.payload)
        .filter(
          ([key]) =>
            !(
              block.blockType === "listening_block" &&
              ["transcript", "audio_asset_id", "audio_variants", "questions", "answer_key", "answerKey"].includes(key)
            ) && !["continuity", "routeContext"].includes(key),
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

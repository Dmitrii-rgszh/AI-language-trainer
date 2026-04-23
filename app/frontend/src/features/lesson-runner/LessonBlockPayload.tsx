import type { LessonBlock } from "../../entities/lesson/model";

type LessonBlockPayloadMode = "all" | "task" | "system";

function getPayloadLabel(key: string, tr: (value: string) => string) {
  const labels: Record<string, string> = {
    brief: "Task",
    items: "Useful phrases",
    reviewItems: "Useful phrases",
    nextStep: "Next step",
    phrases: "Useful phrases",
    prompts: "Try this",
  };

  return tr(labels[key] ?? key.replace(/_/g, " "));
}

export function LessonBlockPayload({
  block,
  mode = "all",
  tr = (value: string) => value,
}: {
  block: LessonBlock;
  mode?: LessonBlockPayloadMode;
  tr?: (value: string) => string;
}) {
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
          taskDrivenInput?: {
            inputRoute?: string;
            inputLabel?: string;
            responseRoute?: string;
            responseLabel?: string;
            title?: string;
            summary?: string;
            bridge?: string;
            closure?: string;
          };
          moduleRotationKeys?: string[];
          moduleRotationTitles?: string[];
          practiceMix?: Array<{
            moduleKey?: string;
            title?: string;
            share?: number;
            emphasis?: string;
            reason?: string;
          }>;
          skillTrajectory?: {
            focusSkill?: string;
            direction?: string;
            summary?: string;
            observedSnapshots?: number;
            signals?: Array<{
              skill?: string;
              direction?: string;
              deltaScore?: number;
              currentScore?: number;
              summary?: string;
            }>;
          };
          strategyMemory?: {
            focusSkill?: string;
            persistenceLevel?: string;
            summary?: string;
            observedSnapshots?: number;
            signals?: Array<{
              skill?: string;
              persistenceLevel?: string;
              averageScore?: number;
              latestScore?: number;
              lowHits?: number;
              summary?: string;
            }>;
          };
          routeCadenceMemory?: {
            status?: string;
            observedPlans?: number;
            completedPlans?: number;
            missedPlans?: number;
            idleDays?: number;
            summary?: string;
            actionHint?: string;
          };
          routeRecoveryMemory?: {
            phase?: string;
            horizonDays?: number;
            focusSkill?: string;
            supportPracticeTitle?: string;
            sessionShape?: string;
            summary?: string;
            actionHint?: string;
            nextPhaseHint?: string;
          };
          skillTrajectorySummary?: string;
          skillTrajectoryFocus?: string;
          skillTrajectoryDirection?: string;
          strategyMemorySummary?: string;
          strategyMemoryFocus?: string;
          strategyMemoryLevel?: string;
          routeCadenceSummary?: string;
          routeCadenceStatus?: string;
          routeRecoverySummary?: string;
          routeRecoveryPhase?: string;
          routeRecoveryActionHint?: string;
          routeRecoveryNextPhaseHint?: string;
          learningBlueprintHeadline?: string;
          learningBlueprintNorthStar?: string;
          learningBlueprintPhaseLabel?: string;
          learningBlueprintSuccessSignal?: string;
          learningBlueprintPillars?: string[];
          dailyRitualHeadline?: string;
          dailyRitualPromise?: string;
          dailyRitualStageIds?: string[];
          routeReentryProgress?: {
            sequenceKey?: string;
            phase?: string;
            focusSkill?: string;
            orderedRoutes?: string[];
            completedRoutes?: string[];
            nextRoute?: string;
            status?: string;
          };
          routeReentryNextRoute?: string;
          routeReentryNextLabel?: string;
          practiceShiftSummary?: string;
          leadPracticeTitle?: string;
          weakestPracticeTitle?: string;
          activeSkillFocus?: string[];
          weakSpotTitles?: string[];
          weakSpotCategories?: string[];
          dueVocabularyWords?: string[];
          carryOverSignalLabel?: string;
          watchSignalLabel?: string;
          ritualSignalType?: string;
          ritualSignalLabel?: string;
          ritualSignalStage?: string;
          ritualSignalWindowStage?: string;
          ritualSignalWindowDays?: number;
          ritualSignalWindowRemainingDays?: number;
          ritualSignalSummary?: string;
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
      {mode !== "task" && routeContext ? (
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
          {routeContext.taskDrivenInput ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">task-driven mission:</span>{" "}
                {routeContext.taskDrivenInput.title ??
                  `${routeContext.taskDrivenInput.inputLabel ?? "input"} -> ${routeContext.taskDrivenInput.responseLabel ?? "response"}`}
              </div>
              {routeContext.taskDrivenInput.summary ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">{routeContext.taskDrivenInput.summary}</div>
              ) : null}
              {(routeContext.taskDrivenInput.inputLabel || routeContext.taskDrivenInput.responseLabel) ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">mission path:</span>{" "}
                  {[routeContext.taskDrivenInput.inputLabel, routeContext.taskDrivenInput.responseLabel]
                    .filter(Boolean)
                    .join(" -> ")}
                </div>
              ) : null}
              {routeContext.taskDrivenInput.bridge ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">bridge:</span> {routeContext.taskDrivenInput.bridge}
                </div>
              ) : null}
              {routeContext.taskDrivenInput.closure ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">closure:</span> {routeContext.taskDrivenInput.closure}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.moduleRotationKeys?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">module rotation:</span>{" "}
              {(routeContext.moduleRotationTitles?.length
                ? routeContext.moduleRotationTitles
                : routeContext.moduleRotationKeys
              ).join(", ")}
            </div>
          ) : null}
          {routeContext.practiceMix?.length ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">practice mix:</span>{" "}
                {routeContext.practiceMix
                  .slice(0, 4)
                  .map((item) =>
                    `${item.title ?? item.moduleKey ?? "module"} ${typeof item.share === "number" ? `${item.share}%` : ""}`.trim(),
                  )
                  .join(", ")}
              </div>
              <div className="mt-3 grid gap-2">
                {routeContext.practiceMix.slice(0, 3).map((item, index) => (
                  <div key={`${item.moduleKey ?? "practice"}-${index}`} className="rounded-2xl bg-coral/6 p-3">
                    <div className="text-sm font-semibold text-ink">
                      {item.title ?? item.moduleKey ?? "Route module"}
                      {typeof item.share === "number" ? ` · ${item.share}%` : ""}
                    </div>
                    {item.reason ? <div className="mt-1 text-sm leading-6 text-slate-700">{item.reason}</div> : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {routeContext.learningBlueprintHeadline ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">blueprint:</span> {routeContext.learningBlueprintHeadline}
              </div>
              {routeContext.learningBlueprintPhaseLabel ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">phase:</span> {routeContext.learningBlueprintPhaseLabel}
                </div>
              ) : null}
              {routeContext.learningBlueprintNorthStar ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">{routeContext.learningBlueprintNorthStar}</div>
              ) : null}
              {routeContext.learningBlueprintPillars?.length ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">pillars:</span> {routeContext.learningBlueprintPillars.join(", ")}
                </div>
              ) : null}
              {routeContext.learningBlueprintSuccessSignal ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">unlock:</span> {routeContext.learningBlueprintSuccessSignal}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.dailyRitualHeadline ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">daily ritual:</span> {routeContext.dailyRitualHeadline}
              </div>
              {routeContext.dailyRitualPromise ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">{routeContext.dailyRitualPromise}</div>
              ) : null}
              {routeContext.dailyRitualStageIds?.length ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">ritual path:</span> {routeContext.dailyRitualStageIds.join(" -> ")}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.skillTrajectorySummary ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">multi-day memory:</span> {routeContext.skillTrajectorySummary}
              </div>
              {routeContext.skillTrajectory?.signals?.length ? (
                <div className="mt-3 grid gap-2">
                  {routeContext.skillTrajectory.signals.slice(0, 3).map((signal, index) => (
                    <div key={`${signal.skill ?? "signal"}-${index}`} className="rounded-2xl bg-coral/6 p-3">
                      <div className="text-sm font-semibold text-ink">
                        {signal.skill ?? "skill"}
                        {typeof signal.currentScore === "number" ? ` · ${signal.currentScore}/100` : ""}
                      </div>
                      <div className="mt-1 text-sm leading-6 text-slate-700">{signal.summary}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.strategyMemorySummary ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">longer strategy memory:</span> {routeContext.strategyMemorySummary}
              </div>
              {routeContext.strategyMemory?.signals?.length ? (
                <div className="mt-3 grid gap-2">
                  {routeContext.strategyMemory.signals.slice(0, 3).map((signal, index) => (
                    <div key={`${signal.skill ?? "memory"}-${index}`} className="rounded-2xl bg-coral/6 p-3">
                      <div className="text-sm font-semibold text-ink">
                        {signal.skill ?? "skill"}
                        {typeof signal.latestScore === "number" ? ` · ${signal.latestScore}/100` : ""}
                      </div>
                      <div className="mt-1 text-sm leading-6 text-slate-700">{signal.summary}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.routeCadenceSummary ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">route cadence:</span> {routeContext.routeCadenceSummary}
              </div>
              {routeContext.routeCadenceMemory?.actionHint ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">re-entry hint:</span> {routeContext.routeCadenceMemory.actionHint}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.routeRecoverySummary ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">recovery arc:</span> {routeContext.routeRecoverySummary}
              </div>
              {routeContext.routeRecoveryMemory?.actionHint ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">recovery hint:</span> {routeContext.routeRecoveryMemory.actionHint}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.ritualSignalWindowStage ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">ritual arc:</span> {routeContext.ritualSignalWindowStage}
              </div>
              {typeof routeContext.ritualSignalWindowRemainingDays === "number" ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">window:</span> {routeContext.ritualSignalWindowRemainingDays} route decisions left
                </div>
              ) : null}
              {routeContext.ritualSignalSummary ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">{routeContext.ritualSignalSummary}</div>
              ) : null}
            </div>
          ) : null}
          {routeContext.routeReentryNextLabel ? (
            <div className="mt-3 rounded-2xl bg-white/78 p-3 text-sm text-slate-700">
              <div>
                <span className="font-semibold text-ink">re-entry sequence:</span> {routeContext.routeReentryNextLabel}
                {Array.isArray(routeContext.routeReentryProgress?.completedRoutes) &&
                Array.isArray(routeContext.routeReentryProgress?.orderedRoutes)
                  ? ` · ${routeContext.routeReentryProgress.completedRoutes.length}/${routeContext.routeReentryProgress.orderedRoutes.length}`
                  : ""}
              </div>
              {routeContext.routeReentryProgress?.status ? (
                <div className="mt-2 text-sm leading-6 text-slate-700">
                  <span className="font-semibold text-ink">sequence state:</span> {routeContext.routeReentryProgress.status}
                </div>
              ) : null}
            </div>
          ) : null}
          {routeContext.practiceShiftSummary ? (
            <div className="mt-3 rounded-2xl bg-coral/6 p-3 text-sm text-slate-700">
              <span className="font-semibold text-ink">practice shift:</span> {routeContext.practiceShiftSummary}
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

      {mode !== "task" && continuityPayload ? (
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

      {mode !== "system" ? Object.entries(block.payload)
        .filter(
          ([key]) =>
            !(
              block.blockType === "listening_block" &&
              ["transcript", "audio_asset_id", "audio_variants", "questions", "answer_key", "answerKey"].includes(key)
            ) &&
            !(
              block.blockType === "reading_block" &&
              ["passage", "passageTitle", "passage_title", "questions", "answer_key", "answerKey"].includes(key)
            ) &&
            !["continuity", "routeContext"].includes(key) &&
            !(
              mode === "task" &&
              [
                "sourceMistakeIds",
                "source_mistake_ids",
                "reviewItems",
                "review_items",
                "targetErrorTypes",
                "target_error_types",
              ].includes(key)
            ),
        )
        .filter(([, value]) =>
          mode !== "task" || Array.isArray(value) || ["boolean", "number", "string"].includes(typeof value),
        )
        .map(([key, value]) => {
          const label = getPayloadLabel(key, tr);

          if (Array.isArray(value)) {
            return (
              <div key={key} className="rounded-2xl bg-white/70 p-4">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-coral">{label}</div>
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
              <span className="font-semibold text-ink">{label}:</span> {String(value)}
            </div>
          );
        }) : null}
    </div>
  );
}

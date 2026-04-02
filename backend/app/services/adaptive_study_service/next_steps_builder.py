from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import AdaptiveLoopStep, ModuleRotationItem, VocabularyReviewItem


def build_next_steps(
    recommendation_lesson_type: str,
    focus_area: str,
    due_vocabulary: Sequence[VocabularyReviewItem],
    listening_focus: str | None,
    module_rotation: Sequence[ModuleRotationItem],
) -> list[AdaptiveLoopStep]:
    steps: list[AdaptiveLoopStep] = []

    if module_rotation and recommendation_lesson_type != "recovery":
        for item in module_rotation[:3]:
            steps.append(
                AdaptiveLoopStep(
                    id=f"adaptive-rotation-{item.module_key}",
                    title=item.title,
                    description=item.reason,
                    route=item.route,
                    step_type=item.module_key,
                )
            )
        return steps

    if recommendation_lesson_type == "recovery":
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-recovery",
                title="Recover your main weak spot",
                description=f"Open a focused drill for {focus_area.replace('_', ' ')} and fix the repeated pattern.",
                route="/lesson-runner",
                step_type="recovery",
            )
        )
    else:
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-lesson",
                title="Return to the main track",
                description="Use the corrected pattern inside a fuller lesson so recovery turns into stable progress.",
                route="/lesson-runner",
                step_type="lesson",
            )
        )

    if due_vocabulary:
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-vocabulary",
                title="Review due vocabulary",
                description=f"Repeat {len(due_vocabulary)} words before the next full lesson block.",
                route="/activity",
                step_type="vocabulary",
            ),
        )

    if listening_focus:
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-listening",
                title="Reinforce listening detail",
                description=f"Use one short audio-first block to stabilize {listening_focus.replace('_', ' ')} before the next full lesson.",
                route="/lesson-runner",
                step_type="listening",
            )
        )

    if recommendation_lesson_type == "recovery":
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-lesson",
                title="Continue with the recommended lesson",
                description="Move forward after recovery so the app keeps pushing the long-term track ahead.",
                route="/lesson-runner",
                step_type="lesson",
            )
        )
    else:
        steps.append(
            AdaptiveLoopStep(
                id="adaptive-step-progress",
                title="Check the refreshed roadmap",
                description="Confirm that the loop has shifted and keep following the next recommendation.",
                route="/dashboard",
                step_type="roadmap",
            )
        )

    return steps

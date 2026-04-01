from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import (
    AdaptiveLoopStep,
    MistakeResolutionSignal,
    ModuleRotationItem,
    VocabularyReviewItem,
)
from app.schemas.progress import LessonHistoryItem


MODULE_ROUTE_MAP = {
    "recovery": "/lesson-runner",
    "lesson": "/lesson-runner",
    "speaking": "/speaking",
    "vocabulary": "/vocabulary",
    "listening": "/activity",
}


def build_module_rotation(
    recommendation_lesson_type: str,
    recommendation_focus_area: str,
    recent_lessons: Sequence[LessonHistoryItem],
    due_vocabulary: Sequence[VocabularyReviewItem],
    listening_focus: str | None,
    mistake_resolution: Sequence[MistakeResolutionSignal],
) -> list[ModuleRotationItem]:
    recent_types = [item.lesson_type for item in recent_lessons[:2]]
    repeated_lesson_pressure = sum(
        1
        for item in recent_types
        if item in {"mixed", "grammar", "professional", "writing", "diagnostic", "recovery"}
    )
    easing_recovery = any(item.status in {"recovering", "stabilizing"} for item in mistake_resolution)

    candidates: list[tuple[str, int, str, str]] = []
    lesson_penalty = 3 if repeated_lesson_pressure >= 1 and easing_recovery else 1
    candidates.append(
        (
            "lesson",
            lesson_penalty,
            "Return to the main lesson flow",
            "Use the broader lesson track to keep corrected patterns alive in context.",
        )
    )

    speaking_priority = (
        0
        if recommendation_focus_area in {"speaking", "grammar", "profession"} or easing_recovery
        else 2
    )
    candidates.append(
        (
            "speaking",
            speaking_priority,
            "Speaking refresh",
            "Short guided speaking keeps the corrected pattern active without forcing a full recovery loop.",
        )
    )

    if due_vocabulary:
        candidates.append(
            (
                "vocabulary",
                0,
                "Vocabulary repetition",
                f"Review {len(due_vocabulary)} due item{'s' if len(due_vocabulary) != 1 else ''} before the next larger module.",
            )
        )

    if listening_focus:
        candidates.append(
            (
                "listening",
                1 if easing_recovery else 0,
                "Listening support",
                f"Add one short audio-first support block for {listening_focus.replace('_', ' ')}.",
            )
        )

    if recommendation_lesson_type == "recovery":
        candidates.insert(
            0,
            (
                "recovery",
                -1,
                "Recovery lesson",
                "Use the focused recovery block first, then rotate back into the broader flow.",
            ),
        )

    ranked = sorted(candidates, key=lambda item: item[1])
    return [
        ModuleRotationItem(
            module_key=module_key,
            title=title,
            reason=reason,
            route=MODULE_ROUTE_MAP[module_key],
            priority=index + 1,
        )
        for index, (module_key, _score, title, reason) in enumerate(ranked)
    ]


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

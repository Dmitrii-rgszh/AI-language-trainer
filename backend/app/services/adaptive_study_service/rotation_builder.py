from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import MistakeResolutionSignal, ModuleRotationItem, VocabularyReviewItem
from app.schemas.progress import LessonHistoryItem
from app.services.adaptive_study_service.rotation_constants import MODULE_ROUTE_MAP


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

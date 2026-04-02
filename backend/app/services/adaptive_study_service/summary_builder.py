from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import VocabularyLoopSummary, VocabularyReviewItem
from app.schemas.mistake import WeakSpot


def build_summary(
    weak_spots: Sequence[WeakSpot],
    due_vocabulary: Sequence[VocabularyReviewItem],
    minutes_completed_today: int,
    listening_focus: str | None,
    vocabulary_summary: VocabularyLoopSummary,
) -> str:
    weak_spot_summary = weak_spots[0].title if weak_spots else "current lesson momentum"
    due_words = len(due_vocabulary)
    listening_part = (
        f" Listening also needs support around {listening_focus.replace('_', ' ')}."
        if listening_focus
        else ""
    )
    vocabulary_part = (
        f" Vocabulary queue: {vocabulary_summary.active_count} active, {vocabulary_summary.mastered_count} mastered."
    )
    return (
        f"Start from {weak_spot_summary}, keep the daily chain moving, "
        f"and clear {due_words} vocabulary review item{'s' if due_words != 1 else ''}."
        f"{listening_part}{vocabulary_part} Minutes completed today: {minutes_completed_today}."
    )

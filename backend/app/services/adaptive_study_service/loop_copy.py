from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import (
    MistakeResolutionSignal,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.mistake import WeakSpot


def build_headline(name: str, focus_area: str) -> str:
    return f"{name}, today's adaptive focus is {focus_area.replace('_', ' ')}."


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


def build_generation_rationale(
    recommendation_lesson_type: str,
    weak_spots: Sequence[WeakSpot],
    vocabulary_summary: VocabularyLoopSummary,
    listening_focus: str | None,
    mistake_resolution: Sequence[MistakeResolutionSignal],
) -> list[str]:
    rationale: list[str] = []
    state_seed = (
        recommendation_lesson_type,
        weak_spots[0].title if weak_spots else "none",
        vocabulary_summary.due_count,
        vocabulary_summary.active_count,
        listening_focus or "none",
        "-".join(item.status for item in mistake_resolution[:2]) or "none",
    )

    if weak_spots:
        rationale.append(
            pick_variant(
                [
                    f"Primary weak spot: {weak_spots[0].title}.",
                    f"Current correction pressure is centered on {weak_spots[0].title}.",
                    f"The loop is still anchored around {weak_spots[0].title}.",
                ],
                *state_seed,
                "weak-spot",
            )
        )

    recovering = [
        item.weak_spot_title
        for item in mistake_resolution
        if item.status in {"recovering", "stabilizing"}
    ]
    if recovering:
        easing_targets = ", ".join(recovering[:2])
        rationale.append(
            pick_variant(
                [
                    f"Recovery pressure is easing for: {easing_targets}.",
                    f"These weak spots are starting to settle: {easing_targets}.",
                    f"Repair intensity can relax a little around: {easing_targets}.",
                ],
                *state_seed,
                easing_targets,
                "recovery-easing",
            )
        )

    if listening_focus:
        focus_label = listening_focus.replace("_", " ")
        rationale.append(
            pick_variant(
                [
                    f"Listening support added for {focus_label}.",
                    f"An audio-first support layer was added for {focus_label}.",
                    f"The loop keeps a listening assist focused on {focus_label}.",
                ],
                *state_seed,
                listening_focus,
                "listening",
            )
        )

    if vocabulary_summary.due_count > 0:
        due_label = f"{vocabulary_summary.due_count} due item{'s' if vocabulary_summary.due_count != 1 else ''}"
        rationale.append(
            pick_variant(
                [
                    f"Vocabulary queue has {due_label}.",
                    f"The repetition queue is carrying {due_label}.",
                    f"Vocabulary review is still live with {due_label}.",
                ],
                *state_seed,
                vocabulary_summary.due_count,
                "vocabulary-due",
            )
        )

    if vocabulary_summary.weakest_category:
        rationale.append(
            pick_variant(
                [
                    f"Most overloaded vocabulary category: {vocabulary_summary.weakest_category}.",
                    f"The heaviest vocabulary carry-over is in {vocabulary_summary.weakest_category}.",
                    f"Vocabulary pressure is leaning most toward {vocabulary_summary.weakest_category}.",
                ],
                *state_seed,
                vocabulary_summary.weakest_category,
                "vocabulary-category",
            )
        )

    rationale.append(
        pick_variant(
            [
                "Next lesson generation is recovery-first.",
                "The next generated step still opens with recovery work.",
                "The loop is keeping recovery at the front of the next generated lesson.",
            ],
            *state_seed,
            "track-recovery",
        )
        if recommendation_lesson_type == "recovery"
        else pick_variant(
            [
                "Next lesson generation returns to the main track.",
                "The next generated step leans back into the main lesson flow.",
                "The loop is ready to move back toward the broader lesson track.",
            ],
            *state_seed,
            "track-main",
        )
    )

    return rationale


def pick_variant(variants: Sequence[str], *seed_parts: object) -> str:
    if not variants:
        return ""

    seed = "|".join(str(part) for part in seed_parts if part is not None)
    if not seed:
        return variants[0]

    weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    index = (weighted_seed + len(seed_parts) * 17) % len(variants)
    return variants[index]

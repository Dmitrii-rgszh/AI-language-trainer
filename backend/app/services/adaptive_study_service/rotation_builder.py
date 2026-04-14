from __future__ import annotations

from collections.abc import Sequence

from app.schemas.adaptive import MistakeResolutionSignal, ModuleRotationItem, VocabularyReviewItem
from app.schemas.progress import LessonHistoryItem
from app.services.adaptive_study_service.rotation_constants import MODULE_ROUTE_MAP


def _normalize_focus_tokens(
    recommendation_focus_area: str,
    active_skill_focus: Sequence[str],
) -> set[str]:
    tokens = {
        token.strip()
        for token in recommendation_focus_area.replace("/", ",").split(",")
        if token.strip()
    }
    tokens.update(skill.strip() for skill in active_skill_focus if skill and skill.strip())
    return tokens


def build_module_rotation(
    recommendation_lesson_type: str,
    recommendation_focus_area: str,
    recent_lessons: Sequence[LessonHistoryItem],
    due_vocabulary: Sequence[VocabularyReviewItem],
    listening_focus: str | None,
    mistake_resolution: Sequence[MistakeResolutionSignal],
    active_skill_focus: Sequence[str] = (),
    preferred_mode: str = "mixed",
    route_seed_source: str | None = None,
) -> list[ModuleRotationItem]:
    focus_tokens = _normalize_focus_tokens(recommendation_focus_area, active_skill_focus)
    recent_types = [item.lesson_type for item in recent_lessons[:2]]
    repeated_lesson_pressure = sum(
        1
        for item in recent_types
        if item in {"mixed", "grammar", "professional", "writing", "diagnostic", "recovery"}
    )
    easing_recovery = any(item.status in {"recovering", "stabilizing"} for item in mistake_resolution)
    continuity_seeded = route_seed_source == "tomorrow_preview"

    candidates: list[tuple[str, int, str, str]] = []
    lesson_penalty = 3 if repeated_lesson_pressure >= 1 and easing_recovery else 1
    if continuity_seeded:
        lesson_penalty += 1
    candidates.append(
        (
            "lesson",
            lesson_penalty,
            "Return to the main lesson flow",
            "Use the broader lesson track to keep corrected patterns alive in context.",
        )
    )

    if "grammar" in focus_tokens:
        candidates.append(
            (
                "grammar",
                -1 if recommendation_focus_area == "grammar" else 0 if "grammar" in active_skill_focus else 1,
                "Grammar anchor",
                "Keep the route structurally clear before widening into a fuller response.",
            )
        )

    speaking_priority = (
        0
        if recommendation_focus_area in {"speaking", "profession"}
        or "speaking" in active_skill_focus
        or preferred_mode == "voice_first"
        or easing_recovery
        else 3 if preferred_mode == "text_first" else 2
    )
    candidates.append(
        (
            "speaking",
            speaking_priority,
            "Speaking refresh",
            "Short guided speaking keeps the corrected pattern active without forcing a full recovery loop.",
        )
    )

    if preferred_mode == "text_first" or "writing" in focus_tokens:
        candidates.append(
            (
                "writing",
                -1 if preferred_mode == "text_first" else 0 if "writing" in active_skill_focus else 1,
                "Writing pass",
                "Use a calmer written response to stabilize structure before the route widens again.",
            )
        )

    if due_vocabulary:
        candidates.append(
            (
                "vocabulary",
                0 if "vocabulary" in focus_tokens or continuity_seeded else 1,
                "Vocabulary repetition",
                f"Review {len(due_vocabulary)} due item{'s' if len(due_vocabulary) != 1 else ''} before the next larger module.",
            )
        )

    if listening_focus:
        candidates.append(
            (
                "listening",
                -1 if recommendation_focus_area == "listening" else 0 if preferred_mode == "voice_first" else 1,
                "Listening support",
                f"Add one short audio-first support block for {listening_focus.replace('_', ' ')}.",
            )
        )

    if preferred_mode == "voice_first" or "pronunciation" in focus_tokens or listening_focus:
        candidates.append(
            (
                "pronunciation",
                -1 if recommendation_focus_area == "pronunciation" or "pronunciation" in active_skill_focus else 1 if preferred_mode == "voice_first" else 2,
                "Pronunciation control",
                "Tighten one sound or rhythm issue while the route is still fresh in memory.",
            )
        )

    if "profession" in focus_tokens:
        candidates.append(
            (
                "profession",
                -1 if recommendation_focus_area == "profession" or "profession" in active_skill_focus else 1,
                "Professional framing",
                "Keep the route anchored in a useful real-world work scenario instead of generic practice.",
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

    deduped_candidates: list[tuple[str, int, str, str]] = []
    seen_keys: set[str] = set()
    for candidate in candidates:
        if candidate[0] in seen_keys:
            continue
        deduped_candidates.append(candidate)
        seen_keys.add(candidate[0])

    ranked = sorted(deduped_candidates, key=lambda item: item[1])
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

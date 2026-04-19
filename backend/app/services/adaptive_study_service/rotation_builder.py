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
    route_cadence_status: str | None = None,
    route_reentry_focus: str | None = None,
    route_reentry_label: str | None = None,
    route_recovery_phase: str | None = None,
    route_recovery_stage: str | None = None,
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
    route_rescue = route_cadence_status == "route_rescue"
    gentle_reentry = route_cadence_status == "gentle_reentry"
    support_reopen_settling = route_recovery_phase == "support_reopen_arc" and route_recovery_stage == "settling_back_in"
    support_reopen_widening = route_recovery_phase == "support_reopen_arc" and route_recovery_stage == "ready_to_expand"

    candidates: list[tuple[str, int, str, str]] = []
    lesson_penalty = 3 if repeated_lesson_pressure >= 1 and easing_recovery else 1
    if continuity_seeded:
        lesson_penalty += 1
    if route_rescue:
        lesson_penalty -= 2
    elif gentle_reentry:
        lesson_penalty -= 1
    if support_reopen_widening:
        lesson_penalty -= 2
    candidates.append(
        (
            "lesson",
            lesson_penalty,
            "Return to the main lesson flow" if not route_rescue else "Gentle route restart",
            (
                "Let the broader daily route lead again while the reopened support lane stays available inside it."
                if support_reopen_widening
                else "Restart the route with one visible win before the wider loop comes back in."
                if route_rescue
                else "Use the broader lesson track to keep corrected patterns alive in context."
            ),
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
    if route_rescue:
        speaking_priority += 2
    elif gentle_reentry:
        speaking_priority += 1
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
                (
                    -1 if preferred_mode == "text_first" else 0 if "writing" in active_skill_focus else 1
                ) + (0 if not route_rescue else -1),
                "Writing pass",
                "Use a calmer written response to stabilize structure before the route widens again.",
            )
        )

    if due_vocabulary:
        candidates.append(
            (
                "vocabulary",
                (0 if "vocabulary" in focus_tokens or continuity_seeded else 1) + (-2 if route_rescue else -1 if gentle_reentry else 0),
                "Vocabulary repetition" if not route_rescue else "Easy vocabulary restart",
                (
                    f"Review {len(due_vocabulary)} due item{'s' if len(due_vocabulary) != 1 else ''} before the next larger module."
                    if not route_rescue
                    else f"Reopen the route through {len(due_vocabulary)} lighter vocabulary item{'s' if len(due_vocabulary) != 1 else ''} before wider pressure returns."
                ),
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
                (
                    -1 if recommendation_focus_area == "pronunciation" or "pronunciation" in active_skill_focus else 1 if preferred_mode == "voice_first" else 2
                ) + (2 if route_rescue else 1 if gentle_reentry else 0),
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

    if route_reentry_focus:
        if all(candidate[0] != route_reentry_focus for candidate in candidates):
            fallback_titles = {
                "grammar": "Grammar anchor next",
                "vocabulary": "Vocabulary support next",
                "speaking": "Speaking refresh next",
                "pronunciation": "Pronunciation control next",
                "writing": "Writing pass next",
                "profession": "Professional framing next",
            }
            fallback_reasons = {
                "grammar": "Sequenced recovery should reopen through grammar support before the wider adaptive rotation returns.",
                "vocabulary": "Sequenced recovery should reopen through vocabulary support before the wider adaptive rotation returns.",
                "speaking": "Sequenced recovery should reopen through speaking support before the wider adaptive rotation returns.",
                "pronunciation": "Sequenced recovery should reopen through pronunciation support before the wider adaptive rotation returns.",
                "writing": "Sequenced recovery should reopen through writing support before the wider adaptive rotation returns.",
                "profession": "Sequenced recovery should reopen through professional support before the wider adaptive rotation returns.",
            }
            candidates.append(
                (
                    route_reentry_focus,
                    -3,
                    fallback_titles.get(route_reentry_focus, f"{route_reentry_focus.capitalize()} next"),
                    fallback_reasons.get(route_reentry_focus, "Sequenced recovery should reopen through this support step before the wider adaptive rotation returns."),
                )
            )
        refreshed_candidates: list[tuple[str, int, str, str]] = []
        for module_key, score, title, reason in candidates:
            if module_key == route_reentry_focus:
                refreshed_reason = reason
                if route_reentry_label and not support_reopen_settling and not support_reopen_widening:
                    refreshed_reason = (
                        f"Sequenced recovery should reopen through {route_reentry_label} before the wider adaptive rotation returns."
                    )
                elif route_reentry_label and support_reopen_settling:
                    refreshed_reason = (
                        f"The reopen arc still needs one more settling pass through {route_reentry_label} before the wider adaptive rotation returns."
                    )
                elif route_reentry_label and support_reopen_widening:
                    refreshed_reason = (
                        f"{route_reentry_label} stays available inside the wider adaptive rotation, but it no longer needs to lead the whole route."
                    )
                refreshed_candidates.append(
                    (
                        module_key,
                        min(score, 0 if support_reopen_widening else -2 if support_reopen_settling else -3),
                        title if not route_reentry_label or support_reopen_widening else f"{title} next",
                        refreshed_reason,
                    )
                )
            else:
                refreshed_candidates.append((module_key, score + (0 if support_reopen_widening else 1), title, reason))
        candidates = refreshed_candidates

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

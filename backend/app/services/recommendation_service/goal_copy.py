from __future__ import annotations

from collections.abc import Sequence

from app.schemas.mistake import WeakSpot


def build_recovery_completed_goal(
    weak_spots: Sequence[WeakSpot],
    profession_track: str,
    due_vocabulary_count: int,
) -> str:
    carry_forward = ", ".join(spot.title for spot in weak_spots) or "recent fixes"
    opener = pick_variant(
        [
            "Recovery loop completed. Return to the main track and apply the corrected patterns in a fuller lesson.",
            "The focused repair pass is done. Step back into the main lesson flow and keep the corrected forms active in context.",
            "Recovery work is finished for now. Rejoin the broader lesson track so the fixed patterns stay alive in real usage.",
        ],
        profession_track,
        due_vocabulary_count,
        carry_forward,
    )
    carry_line = pick_variant(
        [
            f"Carry forward: {carry_forward}.",
            f"Keep these repairs in play: {carry_forward}.",
            f"Do not let these fixes go cold: {carry_forward}.",
        ],
        carry_forward,
        due_vocabulary_count,
        profession_track,
    )
    return f"{opener} {carry_line}"


def build_softened_goal(
    base_goal: str,
    weak_spots: Sequence[WeakSpot],
    resolution_map: dict[str, str],
    due_vocabulary_count: int,
    latest_lesson_type: str | None,
) -> str:
    resolution_summary = ", ".join(
        f"{spot.title} is {resolution_map.get(spot.title, 'active')}"
        for spot in weak_spots
    )
    bridge = pick_variant(
        [
            "Recovery pressure is easing:",
            "The recovery load is starting to soften:",
            "Targeted repair no longer needs to dominate the plan:",
        ],
        resolution_summary,
        due_vocabulary_count,
        latest_lesson_type or "none",
    )
    closer = pick_variant(
        [
            "Keep these patterns alive inside the main lesson flow instead of restarting a hard recovery loop.",
            "Let the main lesson track carry the correction forward rather than forcing another full recovery pass.",
            "Use the broader lesson flow to stabilize these fixes before opening another hard recovery cycle.",
        ],
        resolution_summary,
        due_vocabulary_count,
        latest_lesson_type or "none",
    )
    return f"{base_goal} {bridge} {resolution_summary}. {closer}"


def build_recovery_goal(
    weak_spots: Sequence[WeakSpot],
    priority_text: str,
    due_vocabulary_count: int,
    latest_lesson_type: str | None,
    profession_track: str,
) -> str:
    opener = pick_variant(
        [
            "Short personalized recovery lesson before the next full module.",
            "Use one compact recovery pass before you jump back into the larger lesson track.",
            "Take a focused repair lesson now so the next main module lands on cleaner ground.",
        ],
        priority_text,
        due_vocabulary_count,
        latest_lesson_type or "none",
        profession_track,
    )
    parts = [opener]
    if weak_spots:
        weak_spot_line = pick_variant(
            [
                f"Priority weak spots: {priority_text}.",
                f"Main repair targets right now: {priority_text}.",
                f"These patterns need the first pass of attention: {priority_text}.",
            ],
            priority_text,
            due_vocabulary_count,
            profession_track,
        )
        parts.append(weak_spot_line)
    if due_vocabulary_count:
        vocab_line = pick_variant(
            [
                f"Vocabulary due now: {due_vocabulary_count} item{'s' if due_vocabulary_count != 1 else ''}.",
                f"Vocabulary review queue waiting here: {due_vocabulary_count} item{'s' if due_vocabulary_count != 1 else ''}.",
                f"Fold in {due_vocabulary_count} due vocabulary item{'s' if due_vocabulary_count != 1 else ''} while the repair lesson is still warm.",
            ],
            due_vocabulary_count,
            priority_text,
            latest_lesson_type or "none",
        )
        parts.append(vocab_line)
    return " ".join(parts).strip()


def append_weak_spot_context(
    base_goal: str,
    weak_spots: Sequence[WeakSpot],
    resolution_map: dict[str, str],
    due_vocabulary_count: int,
) -> str:
    priority_line = ", ".join(
        f"{spot.title} ({resolution_map.get(spot.title, 'active')})"
        for spot in weak_spots
    )
    suffix = pick_variant(
        [
            f"Priority weak spots: {priority_line}.",
            f"Keep an eye on these weak spots during the lesson: {priority_line}.",
            f"Use this lesson to hold these patterns steady: {priority_line}.",
        ],
        priority_line,
        due_vocabulary_count,
        len(weak_spots),
    )
    return f"{base_goal} {suffix}"


def append_progress_focus_context(
    base_goal: str,
    *,
    focus_area: str,
    score: int,
    active_skill_focus: Sequence[str],
) -> str:
    suffix = pick_variant(
        [
            f"Live progress now points to {focus_area} as the weakest active skill ({score}/100), so let the next route support it directly.",
            f"The current learner model shows {focus_area} under more pressure ({score}/100), so the next lesson should quietly rebalance around it.",
            f"Right now {focus_area} needs the clearest support ({score}/100), so the main lesson track should lean toward that signal.",
        ],
        focus_area,
        score,
        ",".join(active_skill_focus),
    )
    return f"{base_goal} {suffix}"


def pick_variant(variants: Sequence[str], *seed_parts: object) -> str:
    if not variants:
        return ""
    seed = "|".join(str(part) for part in seed_parts if part is not None)
    if not seed:
        return variants[0]
    weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    index = (weighted_seed + len(seed_parts) * 17) % len(variants)
    return variants[index]

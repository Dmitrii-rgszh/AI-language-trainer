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


def append_skill_trajectory_context(
    base_goal: str,
    *,
    focus_area: str,
    direction: str,
    summary: str,
) -> str:
    suffix = (
        f"Recent multi-day learner memory keeps pointing to {focus_area} as a {direction} signal, so the route should continue to support it deliberately."
        if direction in {"slipping", "stable"}
        else f"Recent learner memory shows {focus_area} improving, so the route can build from that momentum without losing it."
    )
    return f"{base_goal} {suffix} {summary}"


def append_strategy_memory_context(
    base_goal: str,
    *,
    focus_area: str,
    persistence_level: str,
    summary: str,
) -> str:
    suffix = (
        f"Longer learner memory now treats {focus_area} as a persistent strategy signal, so the route should keep coming back to it even when one session looks better."
        if persistence_level == "persistent"
        else f"Longer learner memory keeps seeing {focus_area} as a recurring pressure point, so the route should revisit it deliberately."
        if persistence_level == "recurring"
        else f"Longer learner memory sees {focus_area} emerging as a future weak area, so the route should start protecting it early."
    )
    return f"{base_goal} {suffix} {summary}"


def append_route_recovery_context(
    base_goal: str,
    *,
    phase: str,
    focus_area: str | None,
    summary: str | None,
    action_hint: str | None,
    decision_bias: str | None = None,
    decision_window_days: int | None = None,
    decision_window_stage: str | None = None,
    decision_window_remaining_days: int | None = None,
) -> str:
    resolved_focus = focus_area or "the protected route signal"
    suffix = (
        f"Multi-day recovery strategy is in route_rebuild, so the next recommendation should reopen gently around {resolved_focus} instead of pushing back into hard pressure."
        if phase == "route_rebuild"
        else f"Multi-day recovery strategy is in protected_return, so the next recommendation should stay connected and calm around {resolved_focus} before it widens again."
        if phase == "protected_return"
        else f"Multi-day recovery strategy is in support_reopen_arc, so the next recommendation should let {resolved_focus} come back inside the connected route without turning into another side-track."
        if phase == "support_reopen_arc"
        else f"Multi-day recovery strategy is in skill_repair_cycle, so the next recommendation should keep returning to {resolved_focus} on purpose across several sessions."
        if phase == "skill_repair_cycle"
        else f"Multi-day recovery strategy is in targeted_stabilization, so the next recommendation should keep {resolved_focus} protected before broadening again."
        if phase == "targeted_stabilization"
        else f"Multi-day recovery strategy is in steady_extension, so the next recommendation can keep moving forward while still protecting {resolved_focus}."
    )
    window_suffix = (
        f" Use the next route as the first widening pass: let the broader daily route lead while {resolved_focus} stays available inside the mix."
        if decision_bias == "widening_window" and decision_window_stage == "first_widening_pass"
        else f" Use the next route as a stabilizing widening pass: keep the broader daily route leading while {resolved_focus} stays connected inside the mix."
        if decision_bias == "widening_window" and decision_window_stage == "stabilizing_widening"
        else f" The controlled widening window has already held, so the next route can extend forward again while {resolved_focus} stays available as quiet support."
        if decision_bias == "widening_window" and decision_window_stage == "ready_for_extension"
        else f" For the next {decision_window_remaining_days or decision_window_days} route decisions, keep the broader daily route leading while {resolved_focus} stays available inside the mix."
        if decision_bias == "widening_window" and decision_window_days
        else f" For the next {decision_window_days} route decision, keep {resolved_focus} inside one more connected settling pass before the route widens again."
        if decision_bias == "settling_window" and decision_window_days
        else ""
    )
    extra = " ".join(part for part in [summary, action_hint] if part)
    return f"{base_goal} {suffix}{window_suffix} {extra}".strip()


def append_route_reentry_context(
    base_goal: str,
    *,
    next_route_label: str,
    completed_steps: int,
    total_steps: int,
) -> str:
    suffix = (
        f"Sequenced recovery progression has already cleared {completed_steps} of {total_steps} support steps, "
        f"so the route should reopen through {next_route_label} next."
        if total_steps > 0
        else f"Sequenced recovery progression should reopen through {next_route_label} next."
    )
    return f"{base_goal} {suffix}".strip()


def append_route_entry_memory_context(
    base_goal: str,
    *,
    active_next_route_label: str,
    active_next_route_visits: int,
) -> str:
    suffix = (
        f"{active_next_route_label.capitalize()} has already reopened {active_next_route_visits} times in recent returns, "
        "so the route should reset through the calmer main path before it tries the same support surface again."
    )
    return f"{base_goal} {suffix}".strip()


def append_route_follow_up_context(
    base_goal: str,
    *,
    current_label: str | None,
    follow_up_label: str | None,
    stage_label: str | None,
    summary: str | None,
) -> str:
    stage_prefix = f"{stage_label}. " if stage_label else ""
    if current_label and follow_up_label:
        suffix = (
            f"{stage_prefix}The route should move through {current_label} now, then continue through {follow_up_label} so the sequence stays connected."
        )
    elif follow_up_label:
        suffix = f"{stage_prefix}The next connected step should continue through {follow_up_label}."
    else:
        suffix = stage_prefix.strip()
    extra = f" {summary}" if summary else ""
    return f"{base_goal} {suffix}{extra}".strip()


def pick_variant(variants: Sequence[str], *seed_parts: object) -> str:
    if not variants:
        return ""
    seed = "|".join(str(part) for part in seed_parts if part is not None)
    if not seed:
        return variants[0]
    weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
    index = (weighted_seed + len(seed_parts) * 17) % len(variants)
    return variants[index]

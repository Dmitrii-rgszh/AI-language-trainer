from __future__ import annotations

from app.repositories.lesson_repository import LessonRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.journey_repository import JourneyRepository
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile
from app.services.adaptive_study_service.loop_heuristics import build_progress_trajectory
from app.services.adaptive_study_service.loop_heuristics import build_strategy_memory
from app.services.adaptive_study_service.loop_heuristics import detect_progress_focus
from app.services.recommendation_service.goal_copy import (
    append_progress_focus_context,
    append_route_entry_memory_context,
    append_route_follow_up_context,
    append_route_reentry_context,
    append_route_recovery_context,
    append_skill_trajectory_context,
    append_strategy_memory_context,
    append_weak_spot_context,
    build_recovery_completed_goal,
    build_recovery_goal,
    build_softened_goal,
)
from app.services.shared.recovery_signals import build_resolution_map


def _map_route_to_focus_area(route: str | None) -> str | None:
    return {
        "/grammar": "grammar",
        "/vocabulary": "vocabulary",
        "/speaking": "speaking",
        "/pronunciation": "pronunciation",
        "/writing": "writing",
        "/profession": "profession",
    }.get(route or "")


def _label_route_reentry_route(route: str | None) -> str:
    return {
        "/grammar": "grammar support",
        "/vocabulary": "vocabulary support",
        "/speaking": "speaking support",
        "/pronunciation": "pronunciation support",
        "/writing": "writing support",
        "/profession": "professional support",
    }.get(route or "", "the next support step")


def build_next_recommendation(
    profile: UserProfile,
    lesson_repository: LessonRepository,
    mistake_repository: MistakeRepository,
    vocabulary_repository: VocabularyRepository,
    progress_repository: ProgressRepository | None = None,
    journey_repository: JourneyRepository | None = None,
) -> LessonRecommendation | None:
    weak_spots = mistake_repository.list_weak_spots(profile.id, limit=2)
    mistakes = mistake_repository.list_mistakes(profile.id)
    due_vocabulary = vocabulary_repository.list_due_items(profile.id, limit=3)
    vocabulary_backlinks = vocabulary_repository.list_mistake_backlinks(profile.id, limit=6)
    progress = progress_repository.get_latest_snapshot(profile.id) if progress_repository else None
    recent_progress = progress_repository.list_recent_snapshots(profile.id, limit=5) if progress_repository else []
    latest_completed = lesson_repository.list_recent_completed_lessons(profile.id, limit=1)
    latest_lesson_type = latest_completed[0].lesson_type if latest_completed else None
    resolution_map = build_resolution_map(mistakes, vocabulary_backlinks)
    progress_focus = detect_progress_focus(progress, profile.onboarding_answers.active_skill_focus)
    trajectory = build_progress_trajectory(recent_progress[:3], profile.onboarding_answers.active_skill_focus)
    strategy_memory = build_strategy_memory(recent_progress, profile.onboarding_answers.active_skill_focus)
    journey_state = journey_repository.get_journey_state(profile.id) if journey_repository else None
    route_recovery_memory_value = (
        journey_state.strategy_snapshot.get("routeRecoveryMemory")
        if journey_state
        else None
    )
    route_recovery_memory = (
        route_recovery_memory_value
        if isinstance(route_recovery_memory_value, dict) and route_recovery_memory_value
        else None
    )
    route_recovery_phase = str(route_recovery_memory.get("phase") or "") if route_recovery_memory else ""
    route_recovery_focus = (
        str(route_recovery_memory.get("focusSkill"))
        if route_recovery_memory and route_recovery_memory.get("focusSkill")
        else None
    )
    route_recovery_reopen_stage = (
        str(route_recovery_memory.get("reopenStage"))
        if route_recovery_memory and route_recovery_memory.get("reopenStage")
        else None
    )
    route_recovery_summary = (
        str(route_recovery_memory.get("summary"))
        if route_recovery_memory and route_recovery_memory.get("summary")
        else None
    )
    route_recovery_action_hint = (
        str(route_recovery_memory.get("actionHint"))
        if route_recovery_memory and route_recovery_memory.get("actionHint")
        else None
    )
    route_recovery_decision_bias = (
        str(route_recovery_memory.get("decisionBias"))
        if route_recovery_memory and route_recovery_memory.get("decisionBias")
        else None
    )
    route_recovery_decision_window_days = (
        int(route_recovery_memory.get("decisionWindowDays"))
        if route_recovery_memory and route_recovery_memory.get("decisionWindowDays") is not None
        else None
    )
    route_recovery_decision_window_stage = (
        str(route_recovery_memory.get("decisionWindowStage"))
        if route_recovery_memory and route_recovery_memory.get("decisionWindowStage")
        else None
    )
    route_recovery_decision_window_remaining_days = (
        int(route_recovery_memory.get("decisionWindowRemainingDays"))
        if route_recovery_memory and route_recovery_memory.get("decisionWindowRemainingDays") is not None
        else None
    )
    if (
        route_recovery_phase == "support_reopen_arc"
        and route_recovery_reopen_stage == "ready_to_expand"
        and route_recovery_decision_window_days is None
    ):
        route_recovery_decision_bias = "widening_window"
        route_recovery_decision_window_days = max(
            int(route_recovery_memory.get("horizonDays"))
            if route_recovery_memory and route_recovery_memory.get("horizonDays") is not None
            else 0,
            2,
        )
        route_recovery_decision_window_stage = "first_widening_pass"
        route_recovery_decision_window_remaining_days = route_recovery_decision_window_days
    elif (
        route_recovery_phase == "support_reopen_arc"
        and route_recovery_reopen_stage == "ready_to_expand"
        and route_recovery_decision_window_stage is None
    ):
        route_recovery_decision_window_stage = "first_widening_pass"
        route_recovery_decision_window_remaining_days = (
            route_recovery_decision_window_days
            if route_recovery_decision_window_days is not None
            else max(
                int(route_recovery_memory.get("horizonDays"))
                if route_recovery_memory and route_recovery_memory.get("horizonDays") is not None
                else 0,
                2,
            )
        )
    elif (
        route_recovery_phase == "support_reopen_arc"
        and route_recovery_reopen_stage == "settling_back_in"
        and route_recovery_decision_window_days is None
    ):
        route_recovery_decision_bias = "settling_window"
        route_recovery_decision_window_days = 1
        route_recovery_decision_window_stage = "settling_pass"
        route_recovery_decision_window_remaining_days = 1
    elif (
        route_recovery_phase == "support_reopen_arc"
        and route_recovery_reopen_stage == "settling_back_in"
        and route_recovery_decision_window_stage is None
    ):
        route_recovery_decision_window_stage = "settling_pass"
        route_recovery_decision_window_remaining_days = route_recovery_decision_window_days or 1
    route_reentry_progress_value = (
        journey_state.strategy_snapshot.get("routeReentryProgress")
        if journey_state
        else None
    )
    route_reentry_progress = (
        route_reentry_progress_value
        if isinstance(route_reentry_progress_value, dict) and route_reentry_progress_value
        else None
    )
    route_reentry_next_route = (
        str(route_reentry_progress.get("nextRoute"))
        if route_reentry_progress
        and route_reentry_progress.get("status") != "completed"
        and route_reentry_progress.get("nextRoute")
        else None
    )
    route_reentry_focus = _map_route_to_focus_area(route_reentry_next_route)
    route_reentry_completed_steps = (
        len(route_reentry_progress.get("completedRoutes", []))
        if route_reentry_progress and isinstance(route_reentry_progress.get("completedRoutes"), list)
        else 0
    )
    route_reentry_total_steps = (
        len(route_reentry_progress.get("orderedRoutes", []))
        if route_reentry_progress and isinstance(route_reentry_progress.get("orderedRoutes"), list)
        else 0
    )
    route_reentry_label = _label_route_reentry_route(route_reentry_next_route) if route_reentry_next_route else None
    route_entry_memory_value = (
        journey_state.strategy_snapshot.get("routeEntryMemory")
        if journey_state
        else None
    )
    route_entry_memory = (
        route_entry_memory_value
        if isinstance(route_entry_memory_value, dict) and route_entry_memory_value
        else None
    )
    route_follow_up_memory_value = (
        journey_state.strategy_snapshot.get("routeFollowUpMemory")
        if journey_state
        else None
    )
    route_follow_up_memory = (
        route_follow_up_memory_value
        if isinstance(route_follow_up_memory_value, dict) and route_follow_up_memory_value
        else None
    )
    route_entry_active_next_route = (
        str(route_entry_memory.get("activeNextRoute"))
        if route_entry_memory and route_entry_memory.get("activeNextRoute")
        else None
    )
    route_entry_active_next_route_visits = (
        int(route_entry_memory.get("activeNextRouteVisits"))
        if route_entry_memory and route_entry_memory.get("activeNextRouteVisits")
        else 0
    )
    route_entry_ready_to_reopen = bool(
        route_entry_memory.get("readyToReopenActiveNextRoute")
        if route_entry_memory
        else False
    )
    route_entry_connected_reset_visits = (
        int(route_entry_memory.get("connectedResetVisits"))
        if route_entry_memory and route_entry_memory.get("connectedResetVisits")
        else 0
    )
    repeated_reentry_route = bool(
        route_reentry_next_route
        and route_entry_active_next_route == route_reentry_next_route
        and route_entry_active_next_route_visits >= 2
        and not route_entry_ready_to_reopen
    )
    route_follow_up_current_label = (
        str(route_follow_up_memory.get("currentLabel"))
        if route_follow_up_memory and route_follow_up_memory.get("currentLabel")
        else None
    )
    route_follow_up_label = (
        str(route_follow_up_memory.get("followUpLabel"))
        if route_follow_up_memory and route_follow_up_memory.get("followUpLabel")
        else None
    )
    route_follow_up_stage_label = (
        str(route_follow_up_memory.get("stageLabel"))
        if route_follow_up_memory and route_follow_up_memory.get("stageLabel")
        else None
    )
    route_follow_up_summary = (
        str(route_follow_up_memory.get("summary"))
        if route_follow_up_memory and route_follow_up_memory.get("summary")
        else None
    )
    task_driven_focus = (
        _map_route_to_focus_area(str(route_follow_up_memory.get("currentRoute")))
        if route_follow_up_memory and str(route_follow_up_memory.get("stageLabel") or "") == "Task-driven handoff"
        else None
    )
    if route_entry_ready_to_reopen and route_reentry_label and route_recovery_phase in {
        "protected_return",
        "skill_repair_cycle",
        "targeted_stabilization",
    }:
        route_recovery_phase = "support_reopen_arc"
        route_recovery_focus = route_reentry_focus or route_recovery_focus
        route_recovery_summary = (
            f"The calmer reset has landed across {max(route_entry_connected_reset_visits, 2)} connected passes, so the route can reopen through {route_reentry_label} while staying on the main path."
        )
        route_recovery_action_hint = (
            f"Let {route_reentry_label} return inside the connected route now, but keep the rest of the session from splintering into side-track behavior."
        )
    if not route_follow_up_label and route_reentry_label and route_recovery_phase == "support_reopen_arc":
        route_follow_up_current_label = route_reentry_label
        route_follow_up_label = "daily route"
        route_follow_up_stage_label = route_follow_up_stage_label or "Support reopen"
        route_follow_up_summary = route_follow_up_summary or (
            f"The route should move through {route_reentry_label} now, then reconnect through the daily route so the sequence stays connected."
        )
    prefer_connected_return = route_recovery_phase in {"route_rebuild", "protected_return"}
    prefer_recovery_focus = route_recovery_phase in {"skill_repair_cycle", "targeted_stabilization", "support_reopen_arc"}
    support_reopen_widening = (
        route_recovery_phase == "support_reopen_arc"
        and route_recovery_reopen_stage == "ready_to_expand"
    )
    progress_score_map = {
        "grammar": progress.grammar_score if progress else 0,
        "speaking": progress.speaking_score if progress else 0,
        "listening": progress.listening_score if progress else 0,
        "pronunciation": progress.pronunciation_score if progress else 0,
        "writing": progress.writing_score if progress else 0,
        "profession": progress.profession_score if progress else 0,
    }

    if latest_lesson_type == "recovery":
        recommendation = lesson_repository.get_recommendation(profile.profession_track)
        if not recommendation:
            return None

        recommendation.goal = build_recovery_completed_goal(
            weak_spots=weak_spots,
            profession_track=profile.profession_track,
            due_vocabulary_count=len(due_vocabulary),
        )
        if route_recovery_phase:
            recommendation.focus_area = route_reentry_focus or route_recovery_focus or recommendation.focus_area
            recommendation.goal = append_route_recovery_context(
                recommendation.goal,
                phase=route_recovery_phase,
                focus_area=recommendation.focus_area,
                summary=route_recovery_summary,
                action_hint=route_recovery_action_hint,
                decision_bias=route_recovery_decision_bias,
                decision_window_days=route_recovery_decision_window_days,
                decision_window_stage=route_recovery_decision_window_stage,
                decision_window_remaining_days=route_recovery_decision_window_remaining_days,
            )
            if route_reentry_label:
                recommendation.goal = append_route_reentry_context(
                    recommendation.goal,
                    next_route_label=route_reentry_label,
                    completed_steps=route_reentry_completed_steps,
                    total_steps=route_reentry_total_steps,
                )
        return recommendation

    top_resolution_states = [resolution_map.get(spot.title, "active") for spot in weak_spots]
    active_count = len([state for state in top_resolution_states if state == "active"])
    should_soften_recovery = bool(weak_spots) and bool(top_resolution_states) and (
        top_resolution_states[0] in {"recovering", "stabilizing"} and active_count <= 1
    )

    if should_soften_recovery:
        recommendation = lesson_repository.get_recommendation(profile.profession_track)
        if not recommendation:
            return None

        recommendation.goal = build_softened_goal(
            base_goal=recommendation.goal,
            weak_spots=weak_spots,
            resolution_map=resolution_map,
            due_vocabulary_count=len(due_vocabulary),
            latest_lesson_type=latest_lesson_type,
        )
        if route_recovery_phase and (prefer_connected_return or prefer_recovery_focus):
            recommendation.focus_area = (
                route_recovery_focus
                if repeated_reentry_route
                else recommendation.focus_area
                if support_reopen_widening
                else route_reentry_focus or route_recovery_focus or recommendation.focus_area
            )
            recommendation.goal = append_route_recovery_context(
                recommendation.goal,
                phase=route_recovery_phase,
                focus_area=recommendation.focus_area,
                summary=route_recovery_summary,
                action_hint=route_recovery_action_hint,
                decision_bias=route_recovery_decision_bias,
                decision_window_days=route_recovery_decision_window_days,
            )
            if route_reentry_label and not repeated_reentry_route:
                recommendation.goal = append_route_reentry_context(
                    recommendation.goal,
                    next_route_label=route_reentry_label,
                    completed_steps=route_reentry_completed_steps,
                    total_steps=route_reentry_total_steps,
                )
            if route_follow_up_label:
                recommendation.goal = append_route_follow_up_context(
                    recommendation.goal,
                    current_label=route_follow_up_current_label,
                    follow_up_label=route_follow_up_label,
                    stage_label=route_follow_up_stage_label,
                    summary=route_follow_up_summary,
                )
            if task_driven_focus and not route_recovery_phase:
                recommendation.focus_area = task_driven_focus
            if repeated_reentry_route and route_reentry_label:
                recommendation.goal = append_route_entry_memory_context(
                    recommendation.goal,
                    active_next_route_label=route_reentry_label,
                    active_next_route_visits=route_entry_active_next_route_visits,
                )
                return recommendation
        if progress_focus:
            recommendation.focus_area = progress_focus
            recommendation.goal = append_progress_focus_context(
                recommendation.goal,
                focus_area=progress_focus,
                score=progress_score_map.get(progress_focus, 0),
                active_skill_focus=profile.onboarding_answers.active_skill_focus,
            )
        elif trajectory and trajectory.direction in {"slipping", "stable"}:
            recommendation.focus_area = trajectory.focus_skill
            recommendation.goal = append_skill_trajectory_context(
                recommendation.goal,
                focus_area=trajectory.focus_skill,
                direction=trajectory.direction,
                summary=trajectory.summary,
            )
        elif strategy_memory and strategy_memory.persistence_level in {"persistent", "recurring"}:
            recommendation.focus_area = strategy_memory.focus_skill
            recommendation.goal = append_strategy_memory_context(
                recommendation.goal,
                focus_area=strategy_memory.focus_skill,
                persistence_level=strategy_memory.persistence_level,
                summary=strategy_memory.summary,
            )
        return recommendation

    if weak_spots or due_vocabulary:
        if prefer_connected_return:
            recommendation = lesson_repository.get_recommendation(profile.profession_track)
            if not recommendation:
                return None
            recommendation.focus_area = (
                route_recovery_focus
                if repeated_reentry_route
                else recommendation.focus_area
                if support_reopen_widening
                else route_reentry_focus
                or route_recovery_focus
                or (weak_spots[0].category if weak_spots else None)
                or "vocabulary"
            )
            recommendation.goal = append_route_recovery_context(
                recommendation.goal,
                phase=route_recovery_phase,
                focus_area=recommendation.focus_area,
                summary=route_recovery_summary,
                action_hint=route_recovery_action_hint,
                decision_bias=route_recovery_decision_bias,
                decision_window_days=route_recovery_decision_window_days,
            )
            if route_reentry_label and not repeated_reentry_route:
                recommendation.goal = append_route_reentry_context(
                    recommendation.goal,
                    next_route_label=route_reentry_label,
                    completed_steps=route_reentry_completed_steps,
                    total_steps=route_reentry_total_steps,
                )
            if route_follow_up_label:
                recommendation.goal = append_route_follow_up_context(
                    recommendation.goal,
                    current_label=route_follow_up_current_label,
                    follow_up_label=route_follow_up_label,
                    stage_label=route_follow_up_stage_label,
                    summary=route_follow_up_summary,
                )
            if task_driven_focus and not route_recovery_phase:
                recommendation.focus_area = task_driven_focus
            if repeated_reentry_route and route_reentry_label:
                recommendation.goal = append_route_entry_memory_context(
                    recommendation.goal,
                    active_next_route_label=route_reentry_label,
                    active_next_route_visits=route_entry_active_next_route_visits,
                )
            if weak_spots:
                recommendation.goal = append_weak_spot_context(
                    base_goal=recommendation.goal,
                    weak_spots=weak_spots,
                    resolution_map=resolution_map,
                    due_vocabulary_count=len(due_vocabulary),
                )
            return recommendation

        priority_text = ", ".join(
            f"{spot.title} ({resolution_map.get(spot.title, 'active')})"
            for spot in weak_spots
        )
        recommendation = LessonRecommendation(
            id="adaptive-recovery-recommendation",
            title="Adaptive Recovery Loop",
            lesson_type="recovery",
            goal=build_recovery_goal(
                weak_spots=weak_spots,
                priority_text=priority_text,
                due_vocabulary_count=len(due_vocabulary),
                latest_lesson_type=latest_lesson_type,
                profession_track=profile.profession_track,
            ),
            duration=18 if not due_vocabulary else 22,
            focus_area=(
                route_recovery_focus
                if prefer_recovery_focus and repeated_reentry_route and route_recovery_focus
                else route_reentry_focus
                if prefer_recovery_focus and route_reentry_focus
                else route_recovery_focus
                if prefer_recovery_focus and route_recovery_focus
                else weak_spots[0].category
                if weak_spots
                else "vocabulary"
            ),
        )
        if route_recovery_phase:
            recommendation.goal = append_route_recovery_context(
                recommendation.goal,
                phase=route_recovery_phase,
                focus_area=recommendation.focus_area,
                summary=route_recovery_summary,
                action_hint=route_recovery_action_hint,
                decision_bias=route_recovery_decision_bias,
                decision_window_days=route_recovery_decision_window_days,
            )
            if route_reentry_label and not repeated_reentry_route:
                recommendation.goal = append_route_reentry_context(
                    recommendation.goal,
                    next_route_label=route_reentry_label,
                    completed_steps=route_reentry_completed_steps,
                    total_steps=route_reentry_total_steps,
                )
            if route_follow_up_label:
                recommendation.goal = append_route_follow_up_context(
                    recommendation.goal,
                    current_label=route_follow_up_current_label,
                    follow_up_label=route_follow_up_label,
                    stage_label=route_follow_up_stage_label,
                    summary=route_follow_up_summary,
                )
            if task_driven_focus and not route_recovery_phase:
                recommendation.focus_area = task_driven_focus
            if repeated_reentry_route and route_reentry_label:
                recommendation.goal = append_route_entry_memory_context(
                    recommendation.goal,
                    active_next_route_label=route_reentry_label,
                    active_next_route_visits=route_entry_active_next_route_visits,
                )
        return recommendation

    recommendation = lesson_repository.get_recommendation(profile.profession_track)
    if not recommendation:
        return None

    if route_recovery_phase and (prefer_connected_return or prefer_recovery_focus):
        recommendation.focus_area = (
            route_recovery_focus
            if repeated_reentry_route
            else recommendation.focus_area
            if support_reopen_widening
            else route_reentry_focus or route_recovery_focus or recommendation.focus_area
        )
        recommendation.goal = append_route_recovery_context(
            recommendation.goal,
            phase=route_recovery_phase,
            focus_area=recommendation.focus_area,
            summary=route_recovery_summary,
            action_hint=route_recovery_action_hint,
            decision_bias=route_recovery_decision_bias,
            decision_window_days=route_recovery_decision_window_days,
            decision_window_stage=route_recovery_decision_window_stage,
            decision_window_remaining_days=route_recovery_decision_window_remaining_days,
        )
        if route_reentry_label and not repeated_reentry_route:
            recommendation.goal = append_route_reentry_context(
                recommendation.goal,
                next_route_label=route_reentry_label,
                completed_steps=route_reentry_completed_steps,
                total_steps=route_reentry_total_steps,
            )
        if route_follow_up_label:
            recommendation.goal = append_route_follow_up_context(
                recommendation.goal,
                current_label=route_follow_up_current_label,
                follow_up_label=route_follow_up_label,
                stage_label=route_follow_up_stage_label,
                summary=route_follow_up_summary,
            )
        if task_driven_focus and not route_recovery_phase:
            recommendation.focus_area = task_driven_focus
        if repeated_reentry_route and route_reentry_label:
            recommendation.goal = append_route_entry_memory_context(
                recommendation.goal,
                active_next_route_label=route_reentry_label,
                active_next_route_visits=route_entry_active_next_route_visits,
            )
    elif weak_spots:
        recommendation.goal = append_weak_spot_context(
            base_goal=recommendation.goal,
            weak_spots=weak_spots,
            resolution_map=resolution_map,
            due_vocabulary_count=len(due_vocabulary),
        )
    elif progress_focus:
        recommendation.focus_area = progress_focus
        recommendation.goal = append_progress_focus_context(
            recommendation.goal,
            focus_area=progress_focus,
            score=progress_score_map.get(progress_focus, 0),
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
    elif trajectory and trajectory.direction in {"slipping", "stable"}:
        recommendation.focus_area = trajectory.focus_skill
        recommendation.goal = append_skill_trajectory_context(
            recommendation.goal,
            focus_area=trajectory.focus_skill,
            direction=trajectory.direction,
            summary=trajectory.summary,
        )
    elif strategy_memory and strategy_memory.persistence_level in {"persistent", "recurring"}:
        recommendation.focus_area = strategy_memory.focus_skill
        recommendation.goal = append_strategy_memory_context(
            recommendation.goal,
            focus_area=strategy_memory.focus_skill,
            persistence_level=strategy_memory.persistence_level,
            summary=strategy_memory.summary,
        )

    return recommendation

from __future__ import annotations

from app.schemas.adaptive import (
    AdaptiveStrategyAlignment,
    AdaptiveStudyLoop,
    MistakeVocabularyBacklink,
    MistakeResolutionSignal,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.profile import UserProfile
from app.schemas.progress import LessonHistoryItem, ProgressSnapshot
from app.services.adaptive_study_service.loop_copy import (
    build_generation_rationale,
    build_headline,
    build_summary,
)
from app.services.adaptive_study_service.loop_heuristics import (
    build_mistake_resolution,
    detect_progress_focus,
    detect_listening_focus,
)
from app.services.adaptive_study_service.loop_rotation import (
    build_module_rotation,
    build_next_steps,
)


def build_adaptive_study_loop(
    profile: UserProfile,
    recommendation: LessonRecommendation,
    weak_spots: list[WeakSpot],
    mistakes: list[Mistake],
    progress: ProgressSnapshot | None,
    recent_lessons: list[LessonHistoryItem],
    due_vocabulary: list[VocabularyReviewItem],
    vocabulary_summary: VocabularyLoopSummary,
    vocabulary_backlinks: list[MistakeVocabularyBacklink],
    strategy_alignment: AdaptiveStrategyAlignment | None = None,
) -> AdaptiveStudyLoop:
    mistake_resolution = build_mistake_resolution(mistakes, vocabulary_backlinks)
    listening_focus = detect_listening_focus(progress, weak_spots)
    module_rotation = build_module_rotation(
        recommendation_lesson_type=recommendation.lesson_type,
        recommendation_focus_area=recommendation.focus_area,
        recent_lessons=recent_lessons,
        due_vocabulary=due_vocabulary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
        active_skill_focus=profile.onboarding_answers.active_skill_focus,
        preferred_mode=profile.onboarding_answers.preferred_mode,
        route_seed_source=strategy_alignment.route_seed_source if strategy_alignment else None,
        route_cadence_status=(
            strategy_alignment.route_cadence_memory.status
            if strategy_alignment and strategy_alignment.route_cadence_memory
            else None
        ),
        route_reentry_focus=(
            strategy_alignment.route_reentry_focus
            if strategy_alignment and strategy_alignment.route_reentry_focus
            else None
        ),
        route_reentry_label=(
            strategy_alignment.route_reentry_next_label
            if strategy_alignment and strategy_alignment.route_reentry_next_label
            else None
        ),
        route_recovery_phase=(
            strategy_alignment.route_recovery_memory.phase
            if strategy_alignment and strategy_alignment.route_recovery_memory
            else None
        ),
        route_recovery_stage=(
            strategy_alignment.route_recovery_memory.reopen_stage
            if strategy_alignment and strategy_alignment.route_recovery_memory
            else None
        ),
    )

    progress_focus = detect_progress_focus(progress, profile.onboarding_answers.active_skill_focus)
    trajectory_focus = (
        strategy_alignment.skill_trajectory.focus_skill
        if strategy_alignment and strategy_alignment.skill_trajectory and strategy_alignment.skill_trajectory.direction in {"slipping", "stable"}
        else None
    )
    strategy_memory_focus = (
        strategy_alignment.strategy_memory.focus_skill
        if strategy_alignment and strategy_alignment.strategy_memory and strategy_alignment.strategy_memory.persistence_level in {"persistent", "recurring"}
        else None
    )
    cadence_status = (
        strategy_alignment.route_cadence_memory.status
        if strategy_alignment and strategy_alignment.route_cadence_memory
        else None
    )
    recovery_memory = (
        strategy_alignment.route_recovery_memory
        if strategy_alignment and strategy_alignment.route_recovery_memory
        else None
    )
    route_reentry_focus = (
        strategy_alignment.route_reentry_focus
        if strategy_alignment and strategy_alignment.route_reentry_focus
        else None
    )
    route_reentry_label = (
        strategy_alignment.route_reentry_next_label
        if strategy_alignment and strategy_alignment.route_reentry_next_label
        else None
    )
    if route_reentry_focus:
        focus_area = route_reentry_focus
    elif weak_spots:
        focus_area = weak_spots[0].category
    else:
        focus_area = progress_focus or trajectory_focus or strategy_memory_focus or recommendation.focus_area
    if (
        recovery_memory
        and recovery_memory.phase == "support_reopen_arc"
        and recovery_memory.reopen_stage == "ready_to_expand"
    ):
        focus_area = recommendation.focus_area
    if cadence_status == "route_rescue" and not weak_spots and due_vocabulary:
        focus_area = "vocabulary"
    headline = build_headline(profile.name, focus_area)
    summary = build_summary(
        weak_spots=weak_spots,
        due_vocabulary=due_vocabulary,
        minutes_completed_today=progress.minutes_completed_today if progress else 0,
        listening_focus=listening_focus,
        vocabulary_summary=vocabulary_summary,
    )
    if cadence_status == "route_rescue":
        summary = (
            f"{summary} The route is reopening after a break, so the loop should restart gently before it widens again."
        )
    elif cadence_status == "gentle_reentry":
        summary = (
            f"{summary} The route is reopening after a short pause, so the loop stays calm before it speeds up again."
        )
    if recovery_memory and recovery_memory.summary:
        summary = f"{summary} {recovery_memory.summary}"
        if recovery_memory.phase == "support_reopen_arc" and recovery_memory.reopen_stage == "ready_to_expand":
            summary = f"{summary} The reopened support can stay available, but the broader daily route should lead again."
        elif recovery_memory.phase == "support_reopen_arc" and recovery_memory.reopen_stage == "settling_back_in":
            summary = f"{summary} One more connected settling pass should land before the route widens."
    if route_reentry_label:
        summary = (
            f"{summary} Sequenced recovery is still active, so the next adaptive pass should reopen through {route_reentry_label}."
        )
    generation_rationale = build_generation_rationale(
        recommendation_lesson_type=recommendation.lesson_type,
        weak_spots=weak_spots,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
    )
    if cadence_status == "route_rescue":
        generation_rationale = [
            "Recent route cadence shows a longer break, so the adaptive loop is reopening gently.",
            *generation_rationale,
        ]
    elif cadence_status == "gentle_reentry":
        generation_rationale = [
            "Recent route cadence shows a short pause, so the adaptive loop is staying calmer on re-entry.",
            *generation_rationale,
        ]
    if recovery_memory and recovery_memory.phase:
        generation_rationale = [
            f"Multi-day recovery strategy is currently in {recovery_memory.phase}, so the loop stays aligned with the longer return plan.",
            *generation_rationale,
        ]
        if recovery_memory.phase == "support_reopen_arc" and recovery_memory.reopen_stage == "ready_to_expand":
            generation_rationale = [
                "The reopen arc is ready to widen, so the broader daily route should lead while the reopened support remains inside the mix.",
                *generation_rationale,
            ]
        elif recovery_memory.phase == "support_reopen_arc" and recovery_memory.reopen_stage == "settling_back_in":
            generation_rationale = [
                "The reopen arc still needs one more settling pass, so the adaptive loop keeps the reopened support lane elevated for now.",
                *generation_rationale,
            ]
    if route_reentry_label:
        generation_rationale = [
            f"Sequenced recovery progression is still active, so the loop should reopen through {route_reentry_label} before the wider rotation returns.",
            *generation_rationale,
        ]

    return AdaptiveStudyLoop(
        focus_area=focus_area,
        headline=headline,
        summary=summary,
        recommendation=recommendation,
        weak_spots=weak_spots,
        due_vocabulary=due_vocabulary,
        vocabulary_backlinks=vocabulary_backlinks,
        mistake_resolution=mistake_resolution,
        module_rotation=module_rotation,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        generation_rationale=generation_rationale,
        next_steps=build_next_steps(
            recommendation_lesson_type=recommendation.lesson_type,
            focus_area=focus_area,
            due_vocabulary=due_vocabulary,
            listening_focus=listening_focus,
            module_rotation=module_rotation,
        ),
        strategy_alignment=strategy_alignment,
    )


def derive_generation_rationale(
    recommendation_lesson_type: str,
    weak_spots: list[WeakSpot],
    vocabulary_summary: VocabularyLoopSummary,
    listening_focus: str | None,
    mistake_resolution: list[MistakeResolutionSignal],
) -> list[str]:
    return build_generation_rationale(
        recommendation_lesson_type=recommendation_lesson_type,
        weak_spots=weak_spots,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
    )

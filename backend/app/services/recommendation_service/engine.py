from __future__ import annotations

from app.repositories.lesson_repository import LessonRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile
from app.services.recommendation_service.goal_copy import (
    append_weak_spot_context,
    build_recovery_completed_goal,
    build_recovery_goal,
    build_softened_goal,
)
from app.services.shared.recovery_signals import build_resolution_map


def build_next_recommendation(
    profile: UserProfile,
    lesson_repository: LessonRepository,
    mistake_repository: MistakeRepository,
    vocabulary_repository: VocabularyRepository,
) -> LessonRecommendation | None:
    weak_spots = mistake_repository.list_weak_spots(profile.id, limit=2)
    mistakes = mistake_repository.list_mistakes(profile.id)
    due_vocabulary = vocabulary_repository.list_due_items(profile.id, limit=3)
    vocabulary_backlinks = vocabulary_repository.list_mistake_backlinks(profile.id, limit=6)
    latest_completed = lesson_repository.list_recent_completed_lessons(profile.id, limit=1)
    latest_lesson_type = latest_completed[0].lesson_type if latest_completed else None
    resolution_map = build_resolution_map(mistakes, vocabulary_backlinks)

    if latest_lesson_type == "recovery":
        recommendation = lesson_repository.get_recommendation(profile.profession_track)
        if not recommendation:
            return None

        recommendation.goal = build_recovery_completed_goal(
            weak_spots=weak_spots,
            profession_track=profile.profession_track,
            due_vocabulary_count=len(due_vocabulary),
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
        return recommendation

    if weak_spots or due_vocabulary:
        priority_text = ", ".join(
            f"{spot.title} ({resolution_map.get(spot.title, 'active')})"
            for spot in weak_spots
        )
        return LessonRecommendation(
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
            focus_area=weak_spots[0].category if weak_spots else "vocabulary",
        )

    recommendation = lesson_repository.get_recommendation(profile.profession_track)
    if not recommendation:
        return None

    if weak_spots:
        recommendation.goal = append_weak_spot_context(
            base_goal=recommendation.goal,
            weak_spots=weak_spots,
            resolution_map=resolution_map,
            due_vocabulary_count=len(due_vocabulary),
        )

    return recommendation

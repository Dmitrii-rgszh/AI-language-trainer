from __future__ import annotations

from collections.abc import Sequence

from app.repositories.lesson_repository import LessonRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.journey_repository import JourneyRepository
from app.schemas.adaptive import MistakeVocabularyBacklink
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.profile import UserProfile
from app.services.recommendation_service.engine import build_next_recommendation
from app.services.recommendation_service.goal_copy import (
    append_weak_spot_context,
    build_recovery_completed_goal,
    build_recovery_goal,
    build_softened_goal,
    pick_variant,
)
from app.services.shared.recovery_signals import build_resolution_map


class RecommendationRepository:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
        progress_repository: ProgressRepository | None = None,
        journey_repository: JourneyRepository | None = None,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository
        self._progress_repository = progress_repository
        self._journey_repository = journey_repository

    def get_next_step(self, profile: UserProfile) -> LessonRecommendation | None:
        return build_next_recommendation(
            profile,
            self._lesson_repository,
            self._mistake_repository,
            self._vocabulary_repository,
            self._progress_repository,
            self._journey_repository,
        )

    @classmethod
    def _build_recovery_completed_goal(
        cls,
        weak_spots: Sequence[WeakSpot],
        profession_track: str,
        due_vocabulary_count: int,
    ) -> str:
        return build_recovery_completed_goal(
            weak_spots=weak_spots,
            profession_track=profession_track,
            due_vocabulary_count=due_vocabulary_count,
        )

    @classmethod
    def _build_softened_goal(
        cls,
        base_goal: str,
        weak_spots: Sequence[WeakSpot],
        resolution_map: dict[str, str],
        due_vocabulary_count: int,
        latest_lesson_type: str | None,
    ) -> str:
        return build_softened_goal(
            base_goal=base_goal,
            weak_spots=weak_spots,
            resolution_map=resolution_map,
            due_vocabulary_count=due_vocabulary_count,
            latest_lesson_type=latest_lesson_type,
        )

    @classmethod
    def _build_recovery_goal(
        cls,
        weak_spots: Sequence[WeakSpot],
        priority_text: str,
        due_vocabulary_count: int,
        latest_lesson_type: str | None,
        profession_track: str,
    ) -> str:
        return build_recovery_goal(
            weak_spots=weak_spots,
            priority_text=priority_text,
            due_vocabulary_count=due_vocabulary_count,
            latest_lesson_type=latest_lesson_type,
            profession_track=profession_track,
        )

    @classmethod
    def _append_weak_spot_context(
        cls,
        base_goal: str,
        weak_spots: Sequence[WeakSpot],
        resolution_map: dict[str, str],
        due_vocabulary_count: int,
    ) -> str:
        return append_weak_spot_context(
            base_goal=base_goal,
            weak_spots=weak_spots,
            resolution_map=resolution_map,
            due_vocabulary_count=due_vocabulary_count,
        )

    @staticmethod
    def _build_resolution_map(
        mistakes: Sequence[Mistake],
        vocabulary_backlinks: Sequence[MistakeVocabularyBacklink],
    ) -> dict[str, str]:
        return build_resolution_map(mistakes, vocabulary_backlinks)

    @staticmethod
    def _pick_variant(variants: Sequence[str], *seed_parts: object) -> str:
        return pick_variant(variants, *seed_parts)

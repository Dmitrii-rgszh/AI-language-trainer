from __future__ import annotations

from app.core.errors import ServiceUnavailableError
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.adaptive import (
    AdaptiveStudyLoop,
    MistakeResolutionSignal,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.lesson import LessonRunState
from app.schemas.mistake import WeakSpot
from app.schemas.profile import UserProfile
from app.services.adaptive_study_service.loop_builder import (
    build_adaptive_study_loop,
    derive_generation_rationale,
)
from app.services.adaptive_study_service.vocabulary_hub_builder import build_vocabulary_hub
from app.services.recommendation_service.service import RecommendationService


class AdaptiveStudyService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        recommendation_service: RecommendationService | RecommendationRepository,
        mistake_repository: MistakeRepository,
        progress_repository: ProgressRepository,
        vocabulary_repository: VocabularyRepository,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._recommendation_service = recommendation_service
        self._mistake_repository = mistake_repository
        self._progress_repository = progress_repository
        self._vocabulary_repository = vocabulary_repository

    def get_loop(self, profile: UserProfile) -> AdaptiveStudyLoop | None:
        recommendation = self._recommendation_service.get_next_step(profile)
        if recommendation is None:
            return None

        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
        mistakes = self._mistake_repository.list_mistakes(profile.id)
        progress = self._progress_repository.get_latest_snapshot(profile.id)
        recent_lessons = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=3)
        due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=4)
        vocabulary_summary = self._vocabulary_repository.get_summary(profile.id)
        vocabulary_backlinks = self._vocabulary_repository.list_mistake_backlinks(profile.id, limit=4)

        return build_adaptive_study_loop(
            profile=profile,
            recommendation=recommendation,
            weak_spots=weak_spots,
            mistakes=mistakes,
            progress=progress,
            recent_lessons=recent_lessons,
            due_vocabulary=due_vocabulary,
            vocabulary_summary=vocabulary_summary,
            vocabulary_backlinks=vocabulary_backlinks,
        )

    def review_vocabulary(self, user_id: str, item_id: str, successful: bool) -> VocabularyReviewItem | None:
        return self._vocabulary_repository.review_item(user_id, item_id, successful)

    def get_vocabulary_hub(self, user_id: str) -> VocabularyHub:
        return build_vocabulary_hub(
            summary=self._vocabulary_repository.get_summary(user_id),
            due_items=self._vocabulary_repository.list_due_items(user_id, limit=12),
            recent_items=self._vocabulary_repository.list_recent_items(user_id, limit=10),
            mistake_backlinks=self._vocabulary_repository.list_mistake_backlinks(user_id, limit=6),
        )

    def start_recovery_run(self, profile: UserProfile) -> LessonRunState:
        loop = self.get_loop(profile)
        if loop is None:
            raise ServiceUnavailableError("Adaptive study loop is not available.")

        template = self._lesson_repository.create_recovery_template(
            profession_track=profile.profession_track,
            weak_spots=loop.weak_spots,
            due_vocabulary=loop.due_vocabulary,
            listening_focus=loop.listening_focus,
        )
        lesson_run = self._lesson_runtime_repository.start_lesson_run(
            user_id=profile.id,
            profession_track=profile.profession_track,
            template_id=template.id,
        )
        if lesson_run is None:
            raise ServiceUnavailableError("Recovery lesson could not be generated.")

        return lesson_run

    @staticmethod
    def _build_generation_rationale(
        recommendation_lesson_type: str,
        weak_spots: list[WeakSpot],
        vocabulary_summary: VocabularyLoopSummary,
        listening_focus: str | None,
        mistake_resolution: list[MistakeResolutionSignal],
    ) -> list[str]:
        return derive_generation_rationale(
            recommendation_lesson_type=recommendation_lesson_type,
            weak_spots=weak_spots,
            vocabulary_summary=vocabulary_summary,
            listening_focus=listening_focus,
            mistake_resolution=mistake_resolution,
        )

from app.repositories.lesson_repository import LessonRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile
from app.services.recommendation_service.engine import build_next_recommendation


class RecommendationService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
        progress_repository: ProgressRepository | None = None,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository
        self._progress_repository = progress_repository

    def get_next_step(self, profile: UserProfile) -> LessonRecommendation | None:
        return build_next_recommendation(
            profile,
            self._lesson_repository,
            self._mistake_repository,
            self._vocabulary_repository,
            self._progress_repository,
        )

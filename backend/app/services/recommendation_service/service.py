from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile


class RecommendationService:
    def __init__(self, repository: RecommendationRepository) -> None:
        self._repository = repository

    def get_next_step(self, profile: UserProfile) -> LessonRecommendation | None:
        return self._repository.get_next_step(profile)

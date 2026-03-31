from app.repositories.lesson_repository import LessonRepository
from app.schemas.lesson import Lesson
from app.schemas.profile import UserProfile


class LessonService:
    def __init__(self, repository: LessonRepository) -> None:
        self._repository = repository

    def build_recommended_lesson(self, profile: UserProfile) -> Lesson | None:
        return self._repository.get_recommended_lesson(profile.profession_track)

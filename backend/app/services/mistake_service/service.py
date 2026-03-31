from app.repositories.mistake_repository import MistakeRepository
from app.schemas.mistake import Mistake, WeakSpot


class MistakeService:
    def __init__(self, repository: MistakeRepository) -> None:
        self._repository = repository

    def list_mistakes(self, user_id: str = "user-local-1") -> list[Mistake]:
        return self._repository.list_mistakes(user_id)

    def list_weak_spots(self, user_id: str = "user-local-1") -> list[WeakSpot]:
        return self._repository.list_weak_spots(user_id)

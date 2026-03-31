from app.repositories.listening_repository import ListeningRepository
from app.schemas.listening import ListeningAttempt, ListeningTrend


class ListeningService:
    def __init__(self, repository: ListeningRepository) -> None:
        self._repository = repository

    def list_attempts(self, user_id: str) -> list[ListeningAttempt]:
        return self._repository.list_attempts(user_id)

    def get_trends(self, user_id: str) -> ListeningTrend:
        return self._repository.get_trends(user_id)

from app.repositories.progress_repository import ProgressRepository
from app.schemas.progress import ProgressSnapshot


class ProgressService:
    def __init__(self, repository: ProgressRepository) -> None:
        self._repository = repository

    def get_snapshot(self, user_id: str = "user-local-1") -> ProgressSnapshot:
        snapshot = self._repository.get_latest_snapshot(user_id)
        if snapshot:
            return snapshot

        return ProgressSnapshot(
            id="progress-empty",
            grammar_score=0,
            speaking_score=0,
            listening_score=0,
            pronunciation_score=0,
            writing_score=0,
            profession_score=0,
            regulation_score=0,
            streak=0,
            daily_goal_minutes=25,
            minutes_completed_today=0,
            history=[],
        )

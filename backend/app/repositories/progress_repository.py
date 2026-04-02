from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.lesson_repository import LessonRepository
from app.repositories.progress_mappers import to_progress_snapshot
from app.repositories.progress_queries import load_latest_snapshot
from app.repositories.progress_state import build_progress_snapshot_model
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile
from app.schemas.progress import ProgressSnapshot


class ProgressRepository:
    def __init__(self, session_factory: sessionmaker[Session], lesson_repository: LessonRepository) -> None:
        self._session_factory = session_factory
        self._lesson_repository = lesson_repository

    def get_latest_snapshot(self, user_id: str) -> ProgressSnapshot | None:
        history = self._lesson_repository.list_recent_completed_lessons(user_id)

        with self._session_factory() as session:
            snapshot = load_latest_snapshot(session, user_id)
            if not snapshot:
                return None

            return to_progress_snapshot(snapshot, history)

    def create_snapshot_for_completed_lesson(
        self,
        profile: UserProfile,
        lesson_run: LessonRunState,
        minutes_completed: int | None = None,
    ) -> ProgressSnapshot:
        with self._session_factory() as session:
            latest_model = load_latest_snapshot(session, profile.id)
            snapshot = build_progress_snapshot_model(
                profile,
                lesson_run,
                latest_model,
                minutes_completed=minutes_completed,
            )

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            history = self._lesson_repository.list_recent_completed_lessons(profile.id)
            return to_progress_snapshot(snapshot, history)

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonTemplate
from app.repositories.lesson_template_builders import (
    create_diagnostic_template as build_diagnostic_template,
)
from app.repositories.lesson_template_builders import (
    create_recovery_template as build_recovery_template,
)
from app.repositories.lesson_template_selectors import select_template
from app.repositories.lesson_mappers import (
    to_lesson,
    to_lesson_history_item,
    to_lesson_recommendation,
)
from app.schemas.adaptive import VocabularyReviewItem
from app.schemas.lesson import Lesson, LessonRecommendation
from app.schemas.mistake import WeakSpot
from app.schemas.progress import LessonHistoryItem


class LessonRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_recommended_lesson(self, profession_track: str | None = None) -> Lesson | None:
        with self._session_factory() as session:
            template = select_template(session, profession_track)
            return to_lesson(template) if template else None

    def get_recommendation(self, profession_track: str | None = None) -> LessonRecommendation | None:
        with self._session_factory() as session:
            template = select_template(session, profession_track)
            return to_lesson_recommendation(template) if template else None

    def list_recent_completed_lessons(self, user_id: str, limit: int = 10) -> list[LessonHistoryItem]:
        with self._session_factory() as session:
            statement = (
                select(LessonRun)
                .options(joinedload(LessonRun.template))
                .where(LessonRun.user_id == user_id, LessonRun.completed_at.is_not(None))
                .order_by(LessonRun.completed_at.desc())
                .limit(limit)
            )
            runs = session.scalars(statement).unique().all()
            return [to_lesson_history_item(run) for run in runs]

    def create_recovery_template(
        self,
        profession_track: str,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
        listening_focus: str | None = None,
    ) -> LessonTemplate:
        with self._session_factory() as session:
            return build_recovery_template(
                session,
                profession_track,
                weak_spots,
                due_vocabulary,
                listening_focus,
            )

    def create_diagnostic_template(
        self,
        profession_track: str,
        current_level: str,
        target_level: str,
    ) -> LessonTemplate:
        with self._session_factory() as session:
            return build_diagnostic_template(
                session,
                profession_track,
                current_level,
                target_level,
            )

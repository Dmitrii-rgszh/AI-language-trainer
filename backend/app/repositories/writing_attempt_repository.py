from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.writing_attempt import WritingAttempt as WritingAttemptModel
from app.models.writing_task import WritingTask as WritingTaskModel
from app.schemas.feedback import AITextFeedback, WritingAttempt


class WritingAttemptRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_attempt(
        self,
        *,
        user_id: str,
        task_id: str,
        draft: str,
        feedback: AITextFeedback,
    ) -> WritingAttempt:
        with self._session_factory() as session:
            task = session.get(WritingTaskModel, task_id)
            if task is None:
                raise ValueError(f"Writing task '{task_id}' was not found.")

            model = WritingAttemptModel(
                id=f"writing-attempt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                task_id=task_id,
                draft=draft,
                feedback_summary=feedback.summary,
                feedback_source=feedback.source,
                voice_text=feedback.voice_text,
                voice_language=feedback.voice_language,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_schema(model, task.title)

    def list_attempts(self, user_id: str, limit: int = 12) -> list[WritingAttempt]:
        with self._session_factory() as session:
            statement = (
                select(WritingAttemptModel, WritingTaskModel.title)
                .join(WritingTaskModel, WritingTaskModel.id == WritingAttemptModel.task_id)
                .where(WritingAttemptModel.user_id == user_id)
                .order_by(WritingAttemptModel.created_at.desc())
                .limit(limit)
            )
            rows = session.execute(statement).all()
            return [self._to_schema(model, task_title) for model, task_title in rows]

    @staticmethod
    def _to_schema(model: WritingAttemptModel, task_title: str) -> WritingAttempt:
        return WritingAttempt(
            id=model.id,
            task_id=model.task_id,
            task_title=task_title,
            draft=model.draft,
            feedback_summary=model.feedback_summary,
            feedback_source=model.feedback_source,
            voice_text=model.voice_text,
            voice_language=model.voice_language,
            created_at=model.created_at,
        )

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.speaking_attempt import SpeakingAttempt as SpeakingAttemptModel
from app.models.speaking_scenario import SpeakingScenario as SpeakingScenarioModel
from app.schemas.feedback import AITextFeedback, SpeakingAttempt


class SpeakingAttemptRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_attempt(
        self,
        *,
        user_id: str,
        scenario_id: str,
        input_mode: str,
        transcript: str,
        feedback: AITextFeedback,
    ) -> SpeakingAttempt:
        with self._session_factory() as session:
            scenario = session.get(SpeakingScenarioModel, scenario_id)
            if scenario is None:
                raise ValueError(f"Speaking scenario '{scenario_id}' was not found.")

            model = SpeakingAttemptModel(
                id=f"speaking-attempt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                scenario_id=scenario_id,
                input_mode=input_mode,
                transcript=transcript,
                feedback_summary=feedback.summary,
                feedback_source=feedback.source,
                voice_text=feedback.voice_text,
                voice_language=feedback.voice_language,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_schema(model, scenario.title)

    def list_attempts(self, user_id: str, limit: int = 12) -> list[SpeakingAttempt]:
        with self._session_factory() as session:
            statement = (
                select(SpeakingAttemptModel, SpeakingScenarioModel.title)
                .join(SpeakingScenarioModel, SpeakingScenarioModel.id == SpeakingAttemptModel.scenario_id)
                .where(SpeakingAttemptModel.user_id == user_id)
                .order_by(SpeakingAttemptModel.created_at.desc())
                .limit(limit)
            )
            rows = session.execute(statement).all()
            return [self._to_schema(model, scenario_title) for model, scenario_title in rows]

    @staticmethod
    def _to_schema(model: SpeakingAttemptModel, scenario_title: str) -> SpeakingAttempt:
        return SpeakingAttempt(
            id=model.id,
            scenario_id=model.scenario_id,
            scenario_title=scenario_title,
            input_mode=model.input_mode,
            transcript=model.transcript,
            feedback_summary=model.feedback_summary,
            feedback_source=model.feedback_source,
            voice_text=model.voice_text,
            voice_language=model.voice_language,
            created_at=model.created_at,
        )


from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.pronunciation_attempt import PronunciationAttempt as PronunciationAttemptModel
from app.models.pronunciation_drill import PronunciationDrill as PronunciationDrillModel
from app.schemas.pronunciation import PronunciationAssessment, PronunciationAttempt, PronunciationTrend, TrendPoint


class PronunciationAttemptRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_attempt(
        self,
        *,
        user_id: str,
        target_text: str,
        transcript: str,
        score: int,
        feedback: str,
        weakest_words: list[str],
        focus_issues: list[str],
        drill_id: str | None = None,
        sound_focus: str | None = None,
    ) -> PronunciationAttempt:
        with self._session_factory() as session:
            drill_title = None
            if drill_id:
                drill = session.get(PronunciationDrillModel, drill_id)
                if drill is not None:
                    drill_title = drill.title

            model = PronunciationAttemptModel(
                id=f"pronunciation-attempt-{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                drill_id=drill_id,
                target_text=target_text,
                sound_focus=sound_focus,
                transcript=transcript,
                score=score,
                feedback=feedback,
                weakest_words=weakest_words,
                focus_issues=focus_issues,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_attempt_schema(model, drill_title)

    def list_attempts(self, user_id: str, limit: int = 12) -> list[PronunciationAttempt]:
        with self._session_factory() as session:
            statement = (
                select(PronunciationAttemptModel, PronunciationDrillModel.title)
                .outerjoin(PronunciationDrillModel, PronunciationDrillModel.id == PronunciationAttemptModel.drill_id)
                .where(PronunciationAttemptModel.user_id == user_id)
                .order_by(PronunciationAttemptModel.created_at.desc())
                .limit(limit)
            )
            rows = session.execute(statement).all()
            return [self._to_attempt_schema(model, drill_title) for model, drill_title in rows]

    def get_trends(self, user_id: str, limit: int = 20) -> PronunciationTrend:
        attempts = self.list_attempts(user_id, limit=limit)
        if not attempts:
            return PronunciationTrend(
                average_score=0,
                recent_attempts=0,
                weakest_words=[],
                weakest_sounds=[],
            )

        word_counter = Counter()
        sound_counter = Counter()
        for attempt in attempts:
            word_counter.update(attempt.weakest_words)
            sound_counter.update(attempt.focus_issues)

        return PronunciationTrend(
            average_score=round(sum(attempt.score for attempt in attempts) / len(attempts)),
            recent_attempts=len(attempts),
            weakest_words=[
                TrendPoint(label=label, occurrences=count)
                for label, count in word_counter.most_common(5)
            ],
            weakest_sounds=[
                TrendPoint(label=label, occurrences=count)
                for label, count in sound_counter.most_common(5)
            ],
        )

    @staticmethod
    def _to_attempt_schema(model: PronunciationAttemptModel, drill_title: str | None) -> PronunciationAttempt:
        return PronunciationAttempt(
            id=model.id,
            drill_id=model.drill_id,
            drill_title=drill_title,
            target_text=model.target_text,
            sound_focus=model.sound_focus,
            transcript=model.transcript,
            score=model.score,
            feedback=model.feedback,
            weakest_words=list(model.weakest_words or []),
            focus_issues=list(model.focus_issues or []),
            created_at=model.created_at,
        )

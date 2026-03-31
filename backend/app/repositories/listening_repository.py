from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.models.lesson_run import LessonBlockRun as LessonBlockRunModel
from app.models.lesson_run import LessonRun as LessonRunModel
from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.schemas.listening import ListeningAttempt, ListeningTrend, ListeningTrendPoint


class ListeningRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_attempts(self, user_id: str, limit: int = 12) -> list[ListeningAttempt]:
        with self._session_factory() as session:
            statement = (
                select(LessonBlockRunModel)
                .join(LessonRunModel, LessonRunModel.id == LessonBlockRunModel.lesson_run_id)
                .join(LessonBlockModel, LessonBlockModel.id == LessonBlockRunModel.block_id)
                .options(
                    joinedload(LessonBlockRunModel.block),
                    joinedload(LessonBlockRunModel.lesson_run).joinedload(LessonRunModel.template),
                )
                .where(
                    LessonRunModel.user_id == user_id,
                    LessonBlockModel.block_type == "listening_block",
                    LessonBlockRunModel.completed_at.is_not(None),
                )
                .order_by(LessonBlockRunModel.completed_at.desc())
                .limit(limit)
            )
            return [self._to_attempt(model) for model in session.scalars(statement).unique().all()]

    def get_trends(self, user_id: str, limit: int = 20) -> ListeningTrend:
        attempts = self.list_attempts(user_id, limit=limit)
        if not attempts:
            return ListeningTrend(
                average_score=0,
                recent_attempts=0,
                transcript_support_rate=0,
                weakest_prompts=[],
            )

        prompt_counter = Counter(attempt.prompt_label or attempt.block_title for attempt in attempts if attempt.score < 75)
        transcript_support_rate = round(
            (len([attempt for attempt in attempts if attempt.used_transcript_support]) / len(attempts)) * 100
        )
        return ListeningTrend(
            average_score=round(sum(attempt.score for attempt in attempts) / len(attempts)),
            recent_attempts=len(attempts),
            transcript_support_rate=transcript_support_rate,
            weakest_prompts=[
                ListeningTrendPoint(label=label, occurrences=count)
                for label, count in prompt_counter.most_common(5)
            ],
        )

    @staticmethod
    def _to_attempt(model: LessonBlockRunModel) -> ListeningAttempt:
        payload = model.block.payload if model.block else {}
        prompt_label = None
        if isinstance(payload.get("audio_variants"), list) and payload["audio_variants"]:
            first_variant = payload["audio_variants"][0]
            if isinstance(first_variant, dict):
                prompt_label = first_variant.get("label")

        feedback_summary = model.feedback_summary or ""
        used_transcript_support = "transcript support was used" in feedback_summary.lower()
        answer_summary = (model.user_response or model.transcript or "").strip()
        if len(answer_summary) > 160:
            answer_summary = f"{answer_summary[:157]}..."

        return ListeningAttempt(
            id=model.id,
            lesson_run_id=model.lesson_run_id,
            lesson_title=model.lesson_run.template.title if model.lesson_run and model.lesson_run.template else "Lesson",
            block_title=model.block.title if model.block else "Listening block",
            prompt_label=str(prompt_label) if prompt_label else None,
            answer_summary=answer_summary or "No saved answer",
            score=model.score or 0,
            used_transcript_support=used_transcript_support,
            completed_at=model.completed_at.isoformat() if model.completed_at else "",
        )

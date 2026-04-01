from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.mistake_record import MistakeRecord
from app.repositories.mappers import to_mistake
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.mistake_extraction import ExtractedMistake


WEAK_SPOT_TITLE_MAP = {
    "tense-choice": "Present Perfect vs Past Simple",
    "future-form-choice": "Future Forms for Next Steps",
    "irregular-past": "Irregular Past Forms",
    "subject-verb-agreement": "Subject-Verb Agreement",
    "comparative-form": "Comparative Forms",
    "th-sound": "Sound /th/",
    "feedback-language": "Feedback language for workshops",
    "client-needs-language": "Client needs analysis language",
    "banking-clarity-language": "Banking product clarity",
    "risk-aware-language": "Risk-aware AI explanations",
    "conversation-flow-language": "Everyday conversation flow",
}

WEAK_SPOT_RECOMMENDATION_MAP = {
    "grammar": "Нужен короткий review и speaking drill на опыт и результаты.",
    "pronunciation": "Добавить shadowing и minimal pairs на 5 минут.",
    "profession": "Повторить мягкие формулировки для фасилитации и coaching.",
    "vocabulary": "Добавить повтор слов из ошибок в следующий урок.",
    "speaking": "Сделать короткий guided speaking с delayed feedback.",
    "writing": "Повторить типичные исправления и переписать 2-3 примера.",
}


class MistakeRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_mistakes(self, user_id: str) -> list[Mistake]:
        with self._session_factory() as session:
            statement = (
                select(MistakeRecord)
                .where(MistakeRecord.user_id == user_id)
                .order_by(MistakeRecord.last_seen_at.desc(), MistakeRecord.repetition_count.desc())
            )
            models = session.scalars(statement).all()
            return [to_mistake(model) for model in models]

    def apply_extracted_mistakes(
        self,
        user_id: str,
        source_block_run_map: dict[str, str],
        mistakes: list[ExtractedMistake],
    ) -> list[Mistake]:
        if not mistakes:
            return self.list_mistakes(user_id)

        with self._session_factory() as session:
            now = datetime.utcnow()
            for extracted in mistakes:
                existing = session.scalar(
                    select(MistakeRecord).where(
                        MistakeRecord.user_id == user_id,
                        MistakeRecord.category == extracted.category,
                        MistakeRecord.subtype == extracted.subtype,
                    )
                )
                if existing:
                    existing.original_text = extracted.original_text
                    existing.corrected_text = extracted.corrected_text
                    existing.explanation = extracted.explanation
                    existing.source_module = extracted.source_module
                    existing.source_block_run_id = source_block_run_map.get(extracted.source_module)
                    existing.severity = extracted.severity
                    existing.repetition_count += 1
                    existing.last_seen_at = now
                    continue

                session.add(
                    MistakeRecord(
                        id=f"mistake-{uuid4().hex[:12]}",
                        user_id=user_id,
                        category=extracted.category,
                        subtype=extracted.subtype,
                        source_module=extracted.source_module,
                        source_block_run_id=source_block_run_map.get(extracted.source_module),
                        original_text=extracted.original_text,
                        corrected_text=extracted.corrected_text,
                        explanation=extracted.explanation,
                        severity=extracted.severity,
                        repetition_count=1,
                        created_at=now,
                        last_seen_at=now,
                    )
                )

            session.commit()

        return self.list_mistakes(user_id)

    def list_weak_spots(self, user_id: str, limit: int = 3) -> list[WeakSpot]:
        mistakes = self.list_mistakes(user_id)
        grouped: dict[tuple[str, str], dict[str, int | str]] = defaultdict(
            lambda: {"repetition_count": 0, "category": "", "subtype": ""}
        )

        for mistake in mistakes:
            key = (mistake.category, mistake.subtype)
            grouped[key]["repetition_count"] = int(grouped[key]["repetition_count"]) + mistake.repetition_count
            grouped[key]["category"] = mistake.category
            grouped[key]["subtype"] = mistake.subtype

        ranked = sorted(grouped.values(), key=lambda item: int(item["repetition_count"]), reverse=True)[:limit]
        weak_spots: list[WeakSpot] = []
        for item in ranked:
            category = str(item["category"])
            subtype = str(item["subtype"])
            weak_spots.append(
                WeakSpot(
                    id=f"weak-{subtype}",
                    title=WEAK_SPOT_TITLE_MAP.get(subtype, subtype.replace("-", " ").title()),
                    category=category,
                    recommendation=WEAK_SPOT_RECOMMENDATION_MAP.get(
                        category,
                        "Нужен дополнительный recovery block по этой теме.",
                    ),
                )
            )

        return weak_spots

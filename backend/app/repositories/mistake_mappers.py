from __future__ import annotations

from app.models.mistake_record import MistakeRecord
from app.schemas.mistake import Mistake


def to_mistake(model: MistakeRecord) -> Mistake:
    return Mistake(
        id=model.id,
        category=model.category.value,
        subtype=model.subtype,
        source_module=model.source_module,
        original_text=model.original_text,
        corrected_text=model.corrected_text,
        explanation=model.explanation,
        repetition_count=model.repetition_count,
        last_seen_at=model.last_seen_at,
    )

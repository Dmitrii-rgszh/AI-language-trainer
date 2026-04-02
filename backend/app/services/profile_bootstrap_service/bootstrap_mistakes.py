from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.mistake_record import MistakeRecord
from app.schemas.blueprint import MistakeCategory, MistakeSeverity
from app.schemas.profile import UserProfile

from .selectors import mistake_id
from .types import MistakeSpec, TrackBaselineSpec


def ensure_mistakes(
    session: Session,
    profile: UserProfile,
    spec: TrackBaselineSpec,
    profile_baseline_key: str,
    block_run_ids: dict[str, str],
) -> None:
    now = datetime.utcnow()
    upsert_mistake(
        session,
        profile,
        spec["grammar"],
        mistake_id(profile_baseline_key, "grammar"),
        "mistake-1",
        block_run_ids.get("grammar_block"),
        MistakeCategory.GRAMMAR,
        now - timedelta(days=8),
        now - timedelta(days=1),
    )
    upsert_mistake(
        session,
        profile,
        spec["profession"],
        mistake_id(profile_baseline_key, "profession"),
        "mistake-3",
        block_run_ids.get("profession_block"),
        MistakeCategory.PROFESSION,
        now - timedelta(days=7),
        now - timedelta(days=1),
    )


def upsert_mistake(
    session: Session,
    profile: UserProfile,
    mistake_spec: MistakeSpec,
    record_id: str,
    legacy_id: str,
    block_run_id: str | None,
    category: MistakeCategory,
    created_at: datetime,
    last_seen_at: datetime,
) -> None:
    legacy = session.get(MistakeRecord, legacy_id)
    record = legacy if legacy is not None and legacy.user_id == profile.id else session.get(MistakeRecord, record_id)
    if record is None:
        record = MistakeRecord(
            id=record_id,
            user_id=profile.id,
            category=category,
            subtype=mistake_spec["subtype"],
            source_module=mistake_spec["source_module"],
            source_block_run_id=block_run_id,
            original_text=mistake_spec["original_text"],
            corrected_text=mistake_spec["corrected_text"],
            explanation=mistake_spec["explanation"],
            severity=MistakeSeverity.MEDIUM,
            repetition_count=mistake_spec["repetition_count"],
            created_at=created_at,
            last_seen_at=last_seen_at,
        )
        session.add(record)
        return

    record.user_id = profile.id
    record.category = category
    record.subtype = mistake_spec["subtype"]
    record.source_module = mistake_spec["source_module"]
    record.source_block_run_id = block_run_id
    record.original_text = mistake_spec["original_text"]
    record.corrected_text = mistake_spec["corrected_text"]
    record.explanation = mistake_spec["explanation"]
    record.severity = MistakeSeverity.MEDIUM
    record.repetition_count = mistake_spec["repetition_count"]
    record.created_at = created_at
    record.last_seen_at = last_seen_at

from __future__ import annotations

from collections.abc import Collection
from hashlib import sha1

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonTemplate
from app.models.mistake_record import MistakeRecord
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.models.pronunciation_attempt import PronunciationAttempt
from app.models.vocabulary_item import VocabularyItem

from .constants import (
    BASELINE_PREFIX,
    LEGACY_LESSON_RUN_IDS,
    LEGACY_MISTAKE_IDS,
    LEGACY_PROGRESS_IDS,
    LEGACY_VOCAB_IDS,
)


def baseline_key(user_id: str) -> str:
    return sha1(user_id.encode("utf-8")).hexdigest()[:10]


def mistake_id(value: str, slot: str) -> str:
    return f"{BASELINE_PREFIX}mistake-{value}-{slot}"


def is_bootstrap_id(value: str, legacy_ids: Collection[str]) -> bool:
    return value.startswith(BASELINE_PREFIX) or value in legacy_ids


def has_real_completed_run(session: Session, user_id: str) -> bool:
    runs = session.scalars(
        select(LessonRun).where(LessonRun.user_id == user_id, LessonRun.completed_at.is_not(None))
    ).all()
    return any(
        not is_bootstrap_id(run.id, LEGACY_LESSON_RUN_IDS) and run.recommended_by != "profile_bootstrap"
        for run in runs
    )


def has_real_mistakes(session: Session, user_id: str) -> bool:
    mistakes = session.scalars(select(MistakeRecord).where(MistakeRecord.user_id == user_id)).all()
    return any(not is_bootstrap_id(mistake.id, LEGACY_MISTAKE_IDS) for mistake in mistakes)


def has_real_progress_snapshot(session: Session, user_id: str) -> bool:
    snapshots = session.scalars(select(ProgressSnapshotModel).where(ProgressSnapshotModel.user_id == user_id)).all()
    return any(not is_bootstrap_id(snapshot.id, LEGACY_PROGRESS_IDS) for snapshot in snapshots)


def has_real_vocabulary(session: Session, user_id: str) -> bool:
    items = session.scalars(select(VocabularyItem).where(VocabularyItem.user_id == user_id)).all()
    return any(not is_bootstrap_id(item.id, LEGACY_VOCAB_IDS) for item in items)


def has_real_pronunciation_attempts(session: Session, user_id: str) -> bool:
    attempts = session.scalars(select(PronunciationAttempt).where(PronunciationAttempt.user_id == user_id)).all()
    return any(not attempt.id.startswith(BASELINE_PREFIX) for attempt in attempts)


def build_block_run_index(lesson_run: LessonRun | None) -> dict[str, str]:
    if lesson_run is None or lesson_run.template is None:
        return {}
    block_type_by_id = {block.id: block.block_type for block in lesson_run.template.blocks}
    return {
        block_type_by_id.get(block_run.block_id, block_run.block_id): block_run.id
        for block_run in lesson_run.block_runs
    }


def pick_legacy_or_bootstrap_run(session: Session, user_id: str, value: str) -> LessonRun | None:
    legacy = session.get(LessonRun, "run-1")
    if legacy is not None and legacy.user_id == user_id:
        return legacy
    return session.get(LessonRun, f"{BASELINE_PREFIX}run-{value}")


def select_template(
    session: Session, profession_track: str, preferred_template_id: str
) -> LessonTemplate | None:
    template = session.get(LessonTemplate, preferred_template_id)
    if template is not None:
        return template
    templates = session.scalars(select(LessonTemplate).order_by(LessonTemplate.created_at.asc())).all()
    matching = next((item for item in templates if profession_track in (item.enabled_tracks or [])), None)
    return matching or (templates[0] if templates else None)

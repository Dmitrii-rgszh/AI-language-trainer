from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel


def load_latest_snapshot(session: Session, user_id: str) -> ProgressSnapshotModel | None:
    statement = (
        select(ProgressSnapshotModel)
        .options(selectinload(ProgressSnapshotModel.skill_scores))
        .where(ProgressSnapshotModel.user_id == user_id)
        .order_by(ProgressSnapshotModel.snapshot_date.desc())
        .limit(1)
    )
    return session.scalar(statement)

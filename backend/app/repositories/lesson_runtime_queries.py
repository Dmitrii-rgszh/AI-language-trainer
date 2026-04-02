from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonTemplate
from app.schemas.blueprint import LessonRunStatus


def load_lesson_run(session: Session, user_id: str, run_id: str) -> LessonRun | None:
    statement = (
        select(LessonRun)
        .options(
            joinedload(LessonRun.template).selectinload(LessonTemplate.blocks),
            selectinload(LessonRun.block_runs),
        )
        .where(LessonRun.id == run_id, LessonRun.user_id == user_id)
    )
    return session.scalar(statement)


def load_active_lesson_run(session: Session, user_id: str) -> LessonRun | None:
    statement = (
        select(LessonRun)
        .options(
            joinedload(LessonRun.template).selectinload(LessonTemplate.blocks),
            selectinload(LessonRun.block_runs),
        )
        .where(
            LessonRun.user_id == user_id,
            LessonRun.status.in_([LessonRunStatus.PLANNED, LessonRunStatus.IN_PROGRESS]),
        )
        .order_by(LessonRun.started_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def load_discardable_lesson_run(session: Session, user_id: str, run_id: str) -> LessonRun | None:
    statement = select(LessonRun).where(
        LessonRun.id == run_id,
        LessonRun.user_id == user_id,
        LessonRun.status.in_([LessonRunStatus.PLANNED, LessonRunStatus.IN_PROGRESS]),
    )
    return session.scalar(statement)


def select_lesson_template(
    session: Session,
    profession_track: str | None = None,
    template_id: str | None = None,
) -> LessonTemplate | None:
    if template_id:
        statement = (
            select(LessonTemplate)
            .options(selectinload(LessonTemplate.blocks))
            .where(LessonTemplate.id == template_id)
        )
        return session.scalar(statement)

    statement = (
        select(LessonTemplate)
        .options(selectinload(LessonTemplate.blocks))
        .order_by(LessonTemplate.created_at.asc())
    )
    templates = session.scalars(statement).unique().all()
    if not templates:
        return None

    if profession_track:
        matching = next(
            (template for template in templates if profession_track in (template.enabled_tracks or [])),
            None,
        )
        if matching:
            return matching

    return templates[0]

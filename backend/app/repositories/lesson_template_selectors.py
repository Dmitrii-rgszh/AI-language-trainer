from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.lesson_template import LessonTemplate


def select_template(
    session: Session, profession_track: str | None = None
) -> LessonTemplate | None:
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

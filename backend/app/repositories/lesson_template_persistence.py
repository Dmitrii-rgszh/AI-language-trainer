from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate


def persist_lesson_template(
    session: Session,
    template: LessonTemplate,
    blocks: list[LessonBlockModel],
) -> LessonTemplate:
    session.add_all(blocks)
    session.commit()
    session.refresh(template)
    session.refresh(template, attribute_names=["blocks"])
    return template

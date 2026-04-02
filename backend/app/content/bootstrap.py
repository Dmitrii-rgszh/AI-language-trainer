from __future__ import annotations

from sqlalchemy.orm import Session

from app.content.catalog_upserts import (
    upsert_grammar_topics,
    upsert_profession_topics,
    upsert_profession_tracks,
    upsert_pronunciation_drills,
    upsert_speaking_scenarios,
    upsert_writing_tasks,
)
from app.content.lesson_template_upserts import upsert_lesson_templates


def bootstrap_content(session: Session) -> None:
    grammar_topics = upsert_grammar_topics(session)
    profession_topics = upsert_profession_topics(session)
    upsert_profession_tracks(session)
    upsert_speaking_scenarios(session)
    upsert_pronunciation_drills(session)
    upsert_writing_tasks(session)
    upsert_lesson_templates(
        session,
        grammar_topics=grammar_topics,
        profession_topics=profession_topics,
    )

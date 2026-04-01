from __future__ import annotations

from sqlalchemy import inspect

from app.content.bootstrap import bootstrap_content
from app.core.app_runtime import AppRuntime, build_app_repositories, build_app_runtime, build_app_runtime_dependencies
from app.db.session import SessionLocal, engine


def _bootstrap_content_if_ready() -> None:
    existing_tables = set(inspect(engine).get_table_names())
    required_content_tables = {
        "lesson_templates",
        "lesson_blocks",
        "profession_topics",
        "grammar_topics",
        "profession_tracks",
        "speaking_scenarios",
        "pronunciation_drills",
        "writing_tasks",
    }
    if required_content_tables.issubset(existing_tables):
        with SessionLocal() as bootstrap_session:
            bootstrap_content(bootstrap_session)
            bootstrap_session.commit()


def build_runtime() -> AppRuntime:
    _bootstrap_content_if_ready()
    repositories = build_app_repositories(SessionLocal)
    dependencies = build_app_runtime_dependencies(repositories, SessionLocal)
    return build_app_runtime(repositories, dependencies)

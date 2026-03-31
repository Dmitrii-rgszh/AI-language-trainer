from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.content.bootstrap import bootstrap_content
from app.db.base import Base
from app.models.lesson_template import LessonTemplate

sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))
from seed_demo_data import seed_runtime_data, seed_user


@pytest.fixture
def empty_session_factory(tmp_path) -> Iterator[sessionmaker[Session]]:
    database_path = tmp_path / "empty-test.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, class_=Session)
    Base.metadata.create_all(engine)
    try:
        yield session_factory
    finally:
        engine.dispose()


@pytest.fixture
def seeded_session_factory(tmp_path) -> Iterator[sessionmaker[Session]]:
    database_path = tmp_path / "seeded-test.db"
    engine = create_engine(f"sqlite:///{database_path}", future=True, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, class_=Session)
    Base.metadata.create_all(engine)

    with session_factory() as session:
        bootstrap_content(session)
        session.flush()
        user = seed_user(session)
        template = session.get(LessonTemplate, "template-trainer-daily-flow")
        if not template:
            raise RuntimeError("Expected bootstrapped template-trainer-daily-flow in test fixture.")
        seed_runtime_data(session, user, template)
        session.commit()

    try:
        yield session_factory
    finally:
        engine.dispose()

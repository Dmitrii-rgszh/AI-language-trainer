from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.repositories.lesson_mappers import to_lesson_run_state
from app.repositories.lesson_runtime_mutations import (
    apply_block_result as apply_block_result_update,
    complete_lesson_run as finalize_lesson_run,
    create_lesson_run as create_lesson_run_record,
    discard_lesson_run as discard_lesson_run_record,
)
from app.repositories.lesson_runtime_queries import (
    load_active_lesson_run,
    load_discardable_lesson_run,
    load_lesson_run,
    select_lesson_template,
)
from app.schemas.lesson import BlockResultSubmission, LessonRunState


class LessonRuntimeRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def start_lesson_run(
        self,
        user_id: str,
        profession_track: str | None = None,
        template_id: str | None = None,
    ) -> LessonRunState | None:
        with self._session_factory() as session:
            template = select_lesson_template(
                session,
                profession_track=profession_track,
                template_id=template_id,
            )
            if not template:
                return None

            run_id = create_lesson_run_record(session, user_id, template)
            session.commit()

        return self.get_lesson_run_state(user_id, run_id)

    def complete_lesson_run(
        self,
        user_id: str,
        run_id: str,
        score: int,
        block_results: list[BlockResultSubmission],
    ) -> LessonRunState | None:
        with self._session_factory() as session:
            model = load_lesson_run(session, user_id, run_id)
            if not model:
                return None

            finalize_lesson_run(session, model, user_id, run_id, score, block_results)
            session.commit()

        return self.get_lesson_run_state(user_id, run_id)

    def submit_block_result(
        self,
        user_id: str,
        run_id: str,
        payload: BlockResultSubmission,
    ) -> LessonRunState | None:
        with self._session_factory() as session:
            model = load_lesson_run(session, user_id, run_id)
            if not model:
                return None

            if not apply_block_result_update(model, payload):
                return None

            session.commit()

        return self.get_lesson_run_state(user_id, run_id)

    def get_lesson_run_state(self, user_id: str, run_id: str) -> LessonRunState | None:
        with self._session_factory() as session:
            model = load_lesson_run(session, user_id, run_id)
            if not model:
                return None

            return to_lesson_run_state(model)

    def get_active_lesson_run(self, user_id: str) -> LessonRunState | None:
        with self._session_factory() as session:
            model = load_active_lesson_run(session, user_id)
            if not model:
                return None

            return to_lesson_run_state(model)

    def discard_lesson_run(self, user_id: str, run_id: str) -> bool:
        with self._session_factory() as session:
            model = load_discardable_lesson_run(session, user_id, run_id)
            if not model:
                return False

            discard_lesson_run_record(model)
            session.commit()
            return True

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload, sessionmaker

from app.models.lesson_run import LessonBlockRun, LessonRun
from app.models.lesson_template import LessonTemplate
from app.repositories.mappers import to_lesson_run_state
from app.schemas.blueprint import BlockRunStatus, LessonRunStatus, UserResponseType
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
            template = self._select_template(session, profession_track=profession_track, template_id=template_id)
            if not template:
                return None

            now = datetime.utcnow()
            run_id = f"run-{uuid4().hex[:12]}"
            run = LessonRun(
                id=run_id,
                user_id=user_id,
                template_id=template.id,
                status=LessonRunStatus.IN_PROGRESS,
                recommended_by="app_runtime",
                weak_spot_ids=[],
                started_at=now,
                completed_at=None,
                score=None,
            )
            session.add(run)
            session.flush()

            session.add_all(
                [
                    LessonBlockRun(
                        id=f"block-run-{uuid4().hex[:12]}",
                        lesson_run_id=run.id,
                        block_id=block.id,
                        status=BlockRunStatus.PENDING,
                        user_response_type=UserResponseType.NONE,
                        user_response=None,
                        transcript=None,
                        feedback_summary=None,
                        score=None,
                        started_at=now,
                        completed_at=None,
                    )
                    for block in template.blocks
                ]
            )

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
            statement = (
                select(LessonRun)
                .options(
                    joinedload(LessonRun.template).selectinload(LessonTemplate.blocks),
                    selectinload(LessonRun.block_runs),
                )
                .where(LessonRun.id == run_id, LessonRun.user_id == user_id)
            )
            model = session.scalar(statement)
            if not model:
                return None

            now = datetime.utcnow()
            model.status = LessonRunStatus.COMPLETED
            model.completed_at = now
            model.score = score

            results_by_block_id = {result.block_id: result for result in block_results}
            for block_run in model.block_runs:
                result = results_by_block_id.get(block_run.block_id)
                block_run.status = BlockRunStatus.COMPLETED
                block_run.completed_at = now
                block_run.score = result.score if result and result.score is not None else score
                if result:
                    block_run.user_response_type = UserResponseType(result.user_response_type)
                    block_run.user_response = result.user_response
                    block_run.transcript = result.transcript
                    block_run.feedback_summary = result.feedback_summary

            other_active_runs = session.scalars(
                select(LessonRun).where(
                    LessonRun.user_id == user_id,
                    LessonRun.id != run_id,
                    LessonRun.status.in_([LessonRunStatus.PLANNED, LessonRunStatus.IN_PROGRESS]),
                )
            ).all()
            for other_run in other_active_runs:
                other_run.status = LessonRunStatus.SKIPPED
                other_run.completed_at = now

            session.commit()
            session.refresh(model)

        return self.get_lesson_run_state(user_id, run_id)

    def submit_block_result(
        self,
        user_id: str,
        run_id: str,
        payload: BlockResultSubmission,
    ) -> LessonRunState | None:
        with self._session_factory() as session:
            statement = (
                select(LessonRun)
                .options(
                    joinedload(LessonRun.template).selectinload(LessonTemplate.blocks),
                    selectinload(LessonRun.block_runs),
                )
                .where(LessonRun.id == run_id, LessonRun.user_id == user_id)
            )
            model = session.scalar(statement)
            if not model:
                return None

            block_run = next((item for item in model.block_runs if item.block_id == payload.block_id), None)
            if not block_run:
                return None

            now = datetime.utcnow()
            block_run.status = BlockRunStatus.COMPLETED if (payload.user_response or payload.transcript) else BlockRunStatus.ACTIVE
            block_run.user_response_type = UserResponseType(payload.user_response_type)
            block_run.user_response = payload.user_response
            block_run.transcript = payload.transcript
            block_run.feedback_summary = payload.feedback_summary
            block_run.score = payload.score
            block_run.completed_at = now if block_run.status == BlockRunStatus.COMPLETED else None

            if model.status == LessonRunStatus.PLANNED:
                model.status = LessonRunStatus.IN_PROGRESS

            session.commit()

        return self.get_lesson_run_state(user_id, run_id)

    def get_lesson_run_state(self, user_id: str, run_id: str) -> LessonRunState | None:
        with self._session_factory() as session:
            statement = (
                select(LessonRun)
                .options(
                    joinedload(LessonRun.template).selectinload(LessonTemplate.blocks),
                    selectinload(LessonRun.block_runs),
                )
                .where(LessonRun.id == run_id, LessonRun.user_id == user_id)
            )
            model = session.scalar(statement)
            if not model:
                return None

            return to_lesson_run_state(model)

    def get_active_lesson_run(self, user_id: str) -> LessonRunState | None:
        with self._session_factory() as session:
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
            model = session.scalar(statement)
            if not model:
                return None

            return to_lesson_run_state(model)

    def discard_lesson_run(self, user_id: str, run_id: str) -> bool:
        with self._session_factory() as session:
            model = session.scalar(
                select(LessonRun).where(
                    LessonRun.id == run_id,
                    LessonRun.user_id == user_id,
                    LessonRun.status.in_([LessonRunStatus.PLANNED, LessonRunStatus.IN_PROGRESS]),
                )
            )
            if not model:
                return False

            model.status = LessonRunStatus.SKIPPED
            model.completed_at = datetime.utcnow()
            session.commit()
            return True

    @staticmethod
    def _select_template(
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

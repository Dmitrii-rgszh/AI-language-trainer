from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_run import LessonBlockRun, LessonRun
from app.models.lesson_template import LessonTemplate
from app.schemas.blueprint import BlockRunStatus, LessonRunStatus, UserResponseType
from app.schemas.lesson import BlockResultSubmission


def create_lesson_run(session: Session, user_id: str, template: LessonTemplate) -> str:
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
    return run_id


def complete_lesson_run(
    session: Session,
    model: LessonRun,
    user_id: str,
    run_id: str,
    score: int,
    block_results: list[BlockResultSubmission],
) -> None:
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

    _skip_other_active_runs(session, user_id, run_id, now)


def apply_block_result(model: LessonRun, payload: BlockResultSubmission) -> bool:
    block_run = next((item for item in model.block_runs if item.block_id == payload.block_id), None)
    if not block_run:
        return False

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

    return True


def discard_lesson_run(model: LessonRun) -> None:
    model.status = LessonRunStatus.SKIPPED
    model.completed_at = datetime.utcnow()


def _skip_other_active_runs(session: Session, user_id: str, run_id: str, completed_at: datetime) -> None:
    other_active_runs = session.scalars(
        select(LessonRun).where(
            LessonRun.user_id == user_id,
            LessonRun.id != run_id,
            LessonRun.status.in_([LessonRunStatus.PLANNED, LessonRunStatus.IN_PROGRESS]),
        )
    ).all()
    for other_run in other_active_runs:
        other_run.status = LessonRunStatus.SKIPPED
        other_run.completed_at = completed_at

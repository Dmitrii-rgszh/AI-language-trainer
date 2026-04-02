from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lesson_run import LessonBlockRun, LessonRun
from app.models.lesson_template import LessonTemplate
from app.schemas.blueprint import BlockRunStatus, LessonRunStatus, UserResponseType
from app.schemas.profile import UserProfile

from .constants import BASELINE_PREFIX
from .scoring import block_baseline, run_score
from .selectors import mistake_id, pick_legacy_or_bootstrap_run
from .types import TrackBaselineSpec


def ensure_completed_run(
    session: Session,
    profile: UserProfile,
    template: LessonTemplate,
    spec: TrackBaselineSpec,
    profile_baseline_key: str,
) -> LessonRun:
    run = pick_legacy_or_bootstrap_run(session, profile.id, profile_baseline_key)
    now = datetime.utcnow()
    started_at = now - timedelta(hours=2)
    completed_at = started_at + timedelta(minutes=profile.lesson_duration)

    if run is None:
        run = LessonRun(
            id=f"{BASELINE_PREFIX}run-{profile_baseline_key}",
            user_id=profile.id,
            template_id=template.id,
            status=LessonRunStatus.COMPLETED,
            recommended_by="profile_bootstrap",
            weak_spot_ids=[],
            started_at=started_at,
            completed_at=completed_at,
            score=run_score(profile),
        )
        session.add(run)
        session.flush()
    else:
        run.user_id = profile.id
        run.template_id = template.id
        run.status = LessonRunStatus.COMPLETED
        run.recommended_by = "profile_bootstrap"
        run.started_at = started_at
        run.completed_at = completed_at
        run.score = run_score(profile)

    run.weak_spot_ids = [
        mistake_id(profile_baseline_key, "grammar"),
        mistake_id(profile_baseline_key, "profession"),
    ]

    existing_block_runs = session.scalars(select(LessonBlockRun).where(LessonBlockRun.lesson_run_id == run.id)).all()
    for block_run in existing_block_runs:
        session.delete(block_run)
    session.flush()

    for index, block in enumerate(sorted(template.blocks, key=lambda item: item.position)):
        response_text, feedback_summary, score = block_baseline(block.block_type, spec)
        session.add(
            LessonBlockRun(
                id=f"{BASELINE_PREFIX}block-run-{profile_baseline_key}-{index}",
                lesson_run_id=run.id,
                block_id=block.id,
                status=BlockRunStatus.COMPLETED,
                user_response_type=UserResponseType.TEXT,
                user_response=response_text,
                transcript=None,
                feedback_summary=feedback_summary,
                score=score,
                started_at=started_at + timedelta(minutes=index * 3),
                completed_at=started_at + timedelta(minutes=index * 3 + 2),
            )
        )

    session.flush()
    session.refresh(run)
    session.refresh(run, attribute_names=["block_runs", "template"])
    return run

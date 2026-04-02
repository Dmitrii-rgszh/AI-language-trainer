from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.lesson_run import LessonRun
from app.models.progress_snapshot import ProgressSkillScore
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.schemas.profile import UserProfile

from .constants import BASELINE_PREFIX
from .scoring import skill_score_map


def ensure_progress_snapshot(
    session: Session,
    profile: UserProfile,
    lesson_run: LessonRun | None,
    baseline_key: str,
) -> None:
    legacy = session.get(ProgressSnapshotModel, "snapshot-1")
    snapshot_id = f"{BASELINE_PREFIX}snapshot-{baseline_key}"
    snapshot = legacy if legacy is not None and legacy.user_id == profile.id else session.get(ProgressSnapshotModel, snapshot_id)
    if snapshot is None:
        snapshot = ProgressSnapshotModel(
            id=snapshot_id,
            user_id=profile.id,
            lesson_run_id=lesson_run.id if lesson_run else None,
            snapshot_date=date.today(),
            daily_goal_minutes=profile.lesson_duration,
            minutes_completed_today=max(10, min(180, profile.lesson_duration - 1)),
            streak=max(
                4,
                min(
                    12,
                    round(
                        (
                            profile.speaking_priority
                            + profile.grammar_priority
                            + profile.profession_priority
                        )
                        / 2
                    ),
                ),
            ),
        )
        session.add(snapshot)
    else:
        snapshot.user_id = profile.id
        snapshot.lesson_run_id = lesson_run.id if lesson_run else snapshot.lesson_run_id
        snapshot.snapshot_date = date.today()
        snapshot.daily_goal_minutes = profile.lesson_duration
        snapshot.minutes_completed_today = max(10, min(180, profile.lesson_duration - 1))
        snapshot.streak = max(
            4,
            min(
                12,
                round(
                    (
                        profile.speaking_priority
                        + profile.grammar_priority
                        + profile.profession_priority
                    )
                    / 2
                ),
            ),
        )

    snapshot.skill_scores = []
    for area, score in skill_score_map(profile).items():
        snapshot.skill_scores.append(
            ProgressSkillScore(
                area=area,
                score=score,
                confidence=min(95, score + 16),
                updated_at=datetime.utcnow(),
            )
        )

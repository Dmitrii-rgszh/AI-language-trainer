from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from app.models.progress_snapshot import ProgressSkillScore
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.schemas.blueprint import SkillArea
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile


BLOCK_TYPE_TO_SKILL_AREA = {
    "grammar_block": SkillArea.GRAMMAR,
    "speaking_block": SkillArea.SPEAKING,
    "pronunciation_block": SkillArea.PRONUNCIATION,
    "writing_block": SkillArea.WRITING,
    "listening_block": SkillArea.LISTENING,
    "reading_block": SkillArea.READING,
    "profession_block": SkillArea.PROFESSION_ENGLISH,
}

TRACKED_SKILL_AREAS = (
    SkillArea.GRAMMAR,
    SkillArea.SPEAKING,
    SkillArea.LISTENING,
    SkillArea.PRONUNCIATION,
    SkillArea.WRITING,
    SkillArea.PROFESSION_ENGLISH,
    SkillArea.REGULATION_EU,
)


def build_area_score_map(lesson_run: LessonRunState) -> dict[SkillArea, int]:
    block_type_by_id = {block.id: block.block_type for block in lesson_run.lesson.blocks}
    bucket: dict[SkillArea, list[int]] = {}
    for block_run in lesson_run.block_runs:
        block_type = block_type_by_id.get(block_run.block_id)
        if not block_type:
            continue
        area = BLOCK_TYPE_TO_SKILL_AREA.get(block_type)
        if not area:
            continue
        score = block_run.score if block_run.score is not None else lesson_run.score
        if score is None:
            continue
        bucket.setdefault(area, []).append(score)

    return {area: round(sum(scores) / len(scores)) for area, scores in bucket.items()}


def build_area_attempt_count_map(lesson_run: LessonRunState) -> dict[SkillArea, int]:
    block_type_by_id = {block.id: block.block_type for block in lesson_run.lesson.blocks}
    bucket: dict[SkillArea, int] = {}
    for block_run in lesson_run.block_runs:
        block_type = block_type_by_id.get(block_run.block_id)
        if not block_type:
            continue
        area = BLOCK_TYPE_TO_SKILL_AREA.get(block_type)
        if not area:
            continue
        if block_run.score is None and block_run.status != "completed":
            continue
        bucket[area] = bucket.get(area, 0) + 1
    return bucket


def apply_diagnostic_delta(previous_score: int, previous_confidence: int, checkpoint_score: int) -> tuple[int, int]:
    if checkpoint_score >= 80:
        return min(100, previous_score + 5), min(100, previous_confidence + 8)
    if checkpoint_score >= 65:
        return min(100, previous_score + 2), min(100, previous_confidence + 4)
    if checkpoint_score >= 50:
        return max(0, previous_score - 1), max(0, previous_confidence - 2)
    return max(0, previous_score - 3), max(0, previous_confidence - 5)


def apply_guided_delta(
    previous_score: int,
    previous_confidence: int,
    area_score: int,
    *,
    signal_count: int = 1,
) -> tuple[int, int]:
    clamped_signal_count = max(1, signal_count)
    score_gap = area_score - previous_score

    if area_score >= 85:
        score_delta = 4 if score_gap >= 0 else 1
        confidence_delta = 6
    elif area_score >= 72:
        score_delta = 3 if score_gap >= 8 else 2 if score_gap >= 0 else 1
        confidence_delta = 5
    elif area_score >= 60:
        score_delta = 2 if score_gap >= 6 else 1 if score_gap >= 0 else 0
        confidence_delta = 3
    elif area_score >= 48:
        score_delta = 0 if score_gap >= -4 else -1
        confidence_delta = 1 if score_gap >= 0 else -1
    else:
        score_delta = -2 if previous_score > 0 else 0
        confidence_delta = -3

    if clamped_signal_count >= 2 and score_delta > 0:
        score_delta += 1
    if clamped_signal_count >= 2 and confidence_delta > 0:
        confidence_delta += 1
    if clamped_signal_count >= 3 and confidence_delta > 0:
        confidence_delta += 1

    updated_score = max(0, min(100, previous_score + score_delta))
    updated_confidence = max(0, min(100, previous_confidence + confidence_delta))
    return updated_score, updated_confidence


def build_progress_snapshot_model(
    profile: UserProfile,
    lesson_run: LessonRunState,
    latest_model: ProgressSnapshotModel | None,
    minutes_completed: int | None = None,
) -> ProgressSnapshotModel:
    touched_areas = {
        area
        for block_type in lesson_run.lesson.modules
        if (area := BLOCK_TYPE_TO_SKILL_AREA.get(block_type)) is not None
    }
    area_score_map = build_area_score_map(lesson_run)
    area_attempt_count_map = build_area_attempt_count_map(lesson_run)
    snapshot_date = date.today()

    previous_scores: dict[SkillArea, tuple[int, int]] = {}
    if latest_model:
        for skill_score in latest_model.skill_scores:
            previous_scores[skill_score.area] = (skill_score.score, skill_score.confidence)

    if latest_model and latest_model.snapshot_date == snapshot_date:
        minutes_today = latest_model.minutes_completed_today
        streak = latest_model.streak
    else:
        minutes_today = 0
        streak = 1 if not latest_model else latest_model.streak + 1

    snapshot = ProgressSnapshotModel(
        id=f"snapshot-{uuid4().hex[:12]}",
        user_id=profile.id,
        lesson_run_id=lesson_run.run_id,
        snapshot_date=snapshot_date,
        daily_goal_minutes=profile.lesson_duration,
        minutes_completed_today=min(180, minutes_today + (minutes_completed or lesson_run.lesson.duration)),
        streak=streak,
    )
    snapshot.skill_scores = []

    for area in TRACKED_SKILL_AREAS:
        previous_score, previous_confidence = previous_scores.get(area, (0, 50))
        updated_score = previous_score
        updated_confidence = previous_confidence
        if area in touched_areas:
            if lesson_run.lesson.lesson_type == "diagnostic":
                updated_score, updated_confidence = apply_diagnostic_delta(
                    previous_score,
                    previous_confidence,
                    area_score_map.get(area, lesson_run.score or 70),
                )
            else:
                updated_score, updated_confidence = apply_guided_delta(
                    previous_score,
                    previous_confidence,
                    area_score_map.get(area, lesson_run.score or previous_score or 70),
                    signal_count=area_attempt_count_map.get(area, 1),
                )

        snapshot.skill_scores.append(
            ProgressSkillScore(
                area=area,
                score=updated_score,
                confidence=updated_confidence,
                updated_at=datetime.utcnow(),
            )
        )

    return snapshot

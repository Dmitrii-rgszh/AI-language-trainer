from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.models.progress_snapshot import ProgressSkillScore
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.repositories.lesson_repository import LessonRepository
from app.repositories.mappers import to_progress_snapshot
from app.schemas.blueprint import SkillArea
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile
from app.schemas.progress import ProgressSnapshot

BLOCK_TYPE_TO_SKILL_AREA = {
    "grammar_block": SkillArea.GRAMMAR,
    "speaking_block": SkillArea.SPEAKING,
    "pronunciation_block": SkillArea.PRONUNCIATION,
    "writing_block": SkillArea.WRITING,
    "listening_block": SkillArea.LISTENING,
    "profession_block": SkillArea.PROFESSION_ENGLISH,
}


class ProgressRepository:
    def __init__(self, session_factory: sessionmaker[Session], lesson_repository: LessonRepository) -> None:
        self._session_factory = session_factory
        self._lesson_repository = lesson_repository

    def get_latest_snapshot(self, user_id: str) -> ProgressSnapshot | None:
        history = self._lesson_repository.list_recent_completed_lessons(user_id)

        with self._session_factory() as session:
            snapshot = self._get_latest_snapshot_model(session, user_id)
            if not snapshot:
                return None

            return to_progress_snapshot(snapshot, history)

    def create_snapshot_for_completed_lesson(
        self,
        profile: UserProfile,
        lesson_run: LessonRunState,
        minutes_completed: int | None = None,
    ) -> ProgressSnapshot:
        with self._session_factory() as session:
            latest_model = self._get_latest_snapshot_model(session, profile.id)
            touched_areas = {
                area
                for block_type in lesson_run.lesson.modules
                if (area := BLOCK_TYPE_TO_SKILL_AREA.get(block_type)) is not None
            }
            area_score_map = self._build_area_score_map(lesson_run)
            score_delta = max(2, round((lesson_run.score or 70) / 18))
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

            for area in {
                SkillArea.GRAMMAR,
                SkillArea.SPEAKING,
                SkillArea.LISTENING,
                SkillArea.PRONUNCIATION,
                SkillArea.WRITING,
                SkillArea.PROFESSION_ENGLISH,
                SkillArea.REGULATION_EU,
            }:
                previous_score, previous_confidence = previous_scores.get(area, (0, 50))
                updated_score = previous_score
                updated_confidence = previous_confidence
                if area in touched_areas:
                    if lesson_run.lesson.lesson_type == "diagnostic":
                        updated_score, updated_confidence = self._apply_diagnostic_delta(
                            previous_score,
                            previous_confidence,
                            area_score_map.get(area, lesson_run.score or 70),
                        )
                    else:
                        updated_score = min(100, previous_score + score_delta)
                        updated_confidence = min(100, previous_confidence + 5)

                snapshot.skill_scores.append(
                    ProgressSkillScore(
                        area=area,
                        score=updated_score,
                        confidence=updated_confidence,
                        updated_at=datetime.utcnow(),
                    )
                )

            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            history = self._lesson_repository.list_recent_completed_lessons(profile.id)
            return to_progress_snapshot(snapshot, history)

    @staticmethod
    def _build_area_score_map(lesson_run: LessonRunState) -> dict[SkillArea, int]:
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

    @staticmethod
    def _apply_diagnostic_delta(previous_score: int, previous_confidence: int, checkpoint_score: int) -> tuple[int, int]:
        if checkpoint_score >= 80:
            return min(100, previous_score + 5), min(100, previous_confidence + 8)
        if checkpoint_score >= 65:
            return min(100, previous_score + 2), min(100, previous_confidence + 4)
        if checkpoint_score >= 50:
            return max(0, previous_score - 1), max(0, previous_confidence - 2)
        return max(0, previous_score - 3), max(0, previous_confidence - 5)

    @staticmethod
    def _get_latest_snapshot_model(session: Session, user_id: str) -> ProgressSnapshotModel | None:
        statement = (
            select(ProgressSnapshotModel)
            .options(selectinload(ProgressSnapshotModel.skill_scores))
            .where(ProgressSnapshotModel.user_id == user_id)
            .order_by(ProgressSnapshotModel.snapshot_date.desc())
            .limit(1)
        )
        return session.scalar(statement)

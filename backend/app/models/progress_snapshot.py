from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import SkillArea


class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    __table_args__ = (
        CheckConstraint("daily_goal_minutes >= 0 AND daily_goal_minutes <= 180", name="ck_progress_daily_goal"),
        CheckConstraint(
            "minutes_completed_today >= 0 AND minutes_completed_today <= 180",
            name="ck_progress_minutes_completed",
        ),
        CheckConstraint("streak >= 0", name="ck_progress_streak"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_run_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("lesson_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    snapshot_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    daily_goal_minutes: Mapped[int] = mapped_column(nullable=False)
    minutes_completed_today: Mapped[int] = mapped_column(nullable=False)
    streak: Mapped[int] = mapped_column(nullable=False)

    user = relationship("UserProfile", back_populates="progress_snapshots")
    lesson_run = relationship("LessonRun", back_populates="progress_snapshots")
    skill_scores = relationship(
        "ProgressSkillScore",
        back_populates="progress_snapshot",
        cascade="all, delete-orphan",
    )


class ProgressSkillScore(Base):
    __tablename__ = "progress_skill_scores"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_progress_skill_scores_score"),
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_progress_skill_scores_confidence"),
    )

    progress_snapshot_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("progress_snapshots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    area: Mapped[SkillArea] = mapped_column(
        enum_type(SkillArea, "skill_area_enum"),
        primary_key=True,
    )
    score: Mapped[int] = mapped_column(nullable=False)
    confidence: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)

    progress_snapshot = relationship("ProgressSnapshot", back_populates="skill_scores")


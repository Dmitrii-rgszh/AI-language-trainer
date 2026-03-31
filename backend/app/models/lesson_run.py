from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import BlockRunStatus, LessonRunStatus, UserResponseType


class LessonRun(Base):
    __tablename__ = "lesson_runs"
    __table_args__ = (
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_lesson_runs_score"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("lesson_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[LessonRunStatus] = mapped_column(
        enum_type(LessonRunStatus, "lesson_run_status_enum"),
        nullable=False,
        index=True,
    )
    recommended_by: Mapped[str] = mapped_column(String(128), nullable=False)
    weak_spot_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    score: Mapped[int | None] = mapped_column(nullable=True)

    user = relationship("UserProfile", back_populates="lesson_runs")
    template = relationship("LessonTemplate", back_populates="lesson_runs")
    block_runs = relationship("LessonBlockRun", back_populates="lesson_run", cascade="all, delete-orphan")
    progress_snapshots = relationship("ProgressSnapshot", back_populates="lesson_run")


class LessonBlockRun(Base):
    __tablename__ = "lesson_block_runs"
    __table_args__ = (
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_lesson_block_runs_score"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("lesson_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("lesson_blocks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[BlockRunStatus] = mapped_column(
        enum_type(BlockRunStatus, "block_run_status_enum"),
        nullable=False,
        index=True,
    )
    user_response_type: Mapped[UserResponseType] = mapped_column(
        enum_type(UserResponseType, "user_response_type_enum"),
        nullable=False,
    )
    user_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    lesson_run = relationship("LessonRun", back_populates="block_runs")
    block = relationship("LessonBlock", back_populates="block_runs")
    mistake_records = relationship("MistakeRecord", back_populates="source_block_run")

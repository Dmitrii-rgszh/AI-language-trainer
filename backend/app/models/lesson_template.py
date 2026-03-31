from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin, enum_type
from app.schemas.blueprint import FeedbackMode, LessonType


class LessonTemplate(TimestampMixin, Base):
    __tablename__ = "lesson_templates"
    __table_args__ = (
        CheckConstraint(
            "estimated_duration >= 5 AND estimated_duration <= 120",
            name="ck_lesson_templates_estimated_duration",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_type: Mapped[LessonType] = mapped_column(
        enum_type(LessonType, "lesson_type_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    estimated_duration: Mapped[int] = mapped_column(nullable=False)
    enabled_tracks: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    generation_rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    blocks = relationship(
        "LessonBlock",
        back_populates="lesson_template",
        cascade="all, delete-orphan",
        order_by="LessonBlock.position",
    )
    lesson_runs = relationship("LessonRun", back_populates="template")
    profession_topics = relationship(
        "ProfessionTopic",
        secondary="lesson_template_profession_topics",
        back_populates="lesson_templates",
    )


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"
    __table_args__ = (
        CheckConstraint("position >= 0", name="ck_lesson_blocks_position"),
        CheckConstraint("estimated_minutes >= 1 AND estimated_minutes <= 60", name="ck_lesson_blocks_estimated_minutes"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_template_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("lesson_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    block_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(nullable=False)
    feedback_mode: Mapped[FeedbackMode] = mapped_column(
        enum_type(FeedbackMode, "feedback_mode_enum"),
        nullable=False,
    )
    depends_on_block_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    lesson_template = relationship("LessonTemplate", back_populates="blocks")
    block_runs = relationship("LessonBlockRun", back_populates="block")

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import MistakeCategory, MistakeSeverity


class MistakeRecord(Base):
    __tablename__ = "mistake_records"
    __table_args__ = (
        CheckConstraint("repetition_count >= 1", name="ck_mistake_records_repetition_count"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[MistakeCategory] = mapped_column(
        enum_type(MistakeCategory, "mistake_category_enum"),
        nullable=False,
        index=True,
    )
    subtype: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_block_run_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("lesson_block_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    corrected_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[MistakeSeverity] = mapped_column(
        enum_type(MistakeSeverity, "mistake_severity_enum"),
        nullable=False,
    )
    repetition_count: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)

    user = relationship("UserProfile", back_populates="mistake_records")
    source_block_run = relationship("LessonBlockRun", back_populates="mistake_records")

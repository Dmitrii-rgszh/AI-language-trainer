from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import VocabularyStatus


class VocabularyItem(Base):
    __tablename__ = "vocabulary_items"
    __table_args__ = (
        CheckConstraint("repetition_stage >= 0 AND repetition_stage <= 10", name="ck_vocabulary_repetition_stage"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    word: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    translation: Mapped[str] = mapped_column(String(255), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False, default="seed")
    review_reason: Mapped[str] = mapped_column(Text, nullable=False, default="Core vocabulary practice")
    linked_mistake_subtype: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    linked_mistake_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    learned_status: Mapped[VocabularyStatus] = mapped_column(
        enum_type(VocabularyStatus, "vocabulary_status_enum"),
        nullable=False,
        index=True,
    )
    repetition_stage: Mapped[int] = mapped_column(nullable=False, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    user = relationship("UserProfile", back_populates="vocabulary_items")

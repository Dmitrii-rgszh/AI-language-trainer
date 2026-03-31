from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class PronunciationAttempt(TimestampMixin, Base):
    __tablename__ = "pronunciation_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    drill_id: Mapped[str | None] = mapped_column(
        ForeignKey("pronunciation_drills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    sound_focus: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    weakest_words: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    focus_issues: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    user = relationship("UserProfile", back_populates="pronunciation_attempts")
    drill = relationship("PronunciationDrill")

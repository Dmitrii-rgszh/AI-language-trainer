from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class WritingAttempt(TimestampMixin, Base):
    __tablename__ = "writing_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("writing_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    draft: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_summary: Mapped[str] = mapped_column(Text, nullable=False)
    feedback_source: Mapped[str] = mapped_column(String(16), nullable=False)
    voice_text: Mapped[str] = mapped_column(Text, nullable=False)
    voice_language: Mapped[str] = mapped_column(String(8), nullable=False)

    user = relationship("UserProfile", back_populates="writing_attempts")
    task = relationship("WritingTask")

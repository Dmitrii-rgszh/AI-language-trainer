from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class OnboardingSession(TimestampMixin, Base):
    __tablename__ = "onboarding_sessions"
    __table_args__ = (
        CheckConstraint("current_step >= 0", name="ck_onboarding_sessions_current_step"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proof_lesson")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="proof_lesson")
    proof_lesson_handoff: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    account_draft: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    profile_draft: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    user = relationship("UserAccount", back_populates="onboarding_sessions")

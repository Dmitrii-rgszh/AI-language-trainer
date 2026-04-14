from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class LearnerJourneyState(TimestampMixin, Base):
    __tablename__ = "learner_journey_states"
    __table_args__ = (
        CheckConstraint(
            "time_budget_minutes >= 10 AND time_budget_minutes <= 120",
            name="ck_learner_journey_state_time_budget",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="proof_lesson_complete")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="proof_lesson")
    preferred_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="mixed")
    diagnostic_readiness: Mapped[str] = mapped_column(String(32), nullable=False, default="soft_start")
    time_budget_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    current_focus_area: Mapped[str] = mapped_column(String(64), nullable=False, default="speaking")
    current_strategy_summary: Mapped[str] = mapped_column(Text(), nullable=False, default="")
    next_best_action: Mapped[str] = mapped_column(Text(), nullable=False, default="")
    last_daily_plan_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proof_lesson_handoff: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    strategy_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    user = relationship("UserAccount", back_populates="journey_state")

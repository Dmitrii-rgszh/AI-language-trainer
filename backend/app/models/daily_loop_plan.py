from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class DailyLoopPlan(TimestampMixin, Base):
    __tablename__ = "daily_loop_plans"
    __table_args__ = (
        UniqueConstraint("user_id", "plan_date_key", name="uq_daily_loop_plans_user_date"),
        CheckConstraint(
            "time_budget_minutes >= 10 AND time_budget_minutes <= 120",
            name="ck_daily_loop_plans_time_budget",
        ),
        CheckConstraint(
            "estimated_minutes >= 10 AND estimated_minutes <= 120",
            name="ck_daily_loop_plans_estimated_minutes",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_date_key: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="first_path")
    session_kind: Mapped[str] = mapped_column(String(32), nullable=False, default="recommended")
    focus_area: Mapped[str] = mapped_column(String(64), nullable=False, default="speaking")
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)
    why_this_now: Mapped[str] = mapped_column(Text(), nullable=False)
    next_step_hint: Mapped[str] = mapped_column(Text(), nullable=False)
    preferred_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="mixed")
    time_budget_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    recommended_lesson_type: Mapped[str] = mapped_column(String(32), nullable=False, default="core")
    recommended_lesson_title: Mapped[str] = mapped_column(String(255), nullable=False, default="Daily lesson")
    lesson_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    completion_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user = relationship("UserAccount", back_populates="daily_loop_plans")

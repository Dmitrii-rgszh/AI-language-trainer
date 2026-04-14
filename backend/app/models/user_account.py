from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin


class UserAccount(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    login: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    onboarding = relationship("UserOnboarding", back_populates="user", cascade="all, delete-orphan", uselist=False)
    onboarding_sessions = relationship("OnboardingSession", back_populates="user")
    journey_state = relationship("LearnerJourneyState", back_populates="user", cascade="all, delete-orphan", uselist=False)
    daily_loop_plans = relationship("DailyLoopPlan", back_populates="user", cascade="all, delete-orphan")

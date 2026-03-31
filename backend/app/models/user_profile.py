from __future__ import annotations

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import TimestampMixin, enum_type
from app.schemas.blueprint import ProfessionDomain


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"
    __table_args__ = (
        CheckConstraint("lesson_duration >= 10 AND lesson_duration <= 90", name="ck_user_profiles_lesson_duration"),
        CheckConstraint(
            "speaking_priority >= 1 AND speaking_priority <= 10",
            name="ck_user_profiles_speaking_priority",
        ),
        CheckConstraint(
            "grammar_priority >= 1 AND grammar_priority <= 10",
            name="ck_user_profiles_grammar_priority",
        ),
        CheckConstraint(
            "profession_priority >= 1 AND profession_priority <= 10",
            name="ck_user_profiles_profession_priority",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    native_language: Mapped[str] = mapped_column(String(32), nullable=False)
    current_level: Mapped[str] = mapped_column(String(16), nullable=False)
    target_level: Mapped[str] = mapped_column(String(16), nullable=False)
    profession_track: Mapped[ProfessionDomain] = mapped_column(
        enum_type(ProfessionDomain, "profession_domain_enum"),
        nullable=False,
    )
    preferred_ui_language: Mapped[str] = mapped_column(String(16), nullable=False)
    preferred_explanation_language: Mapped[str] = mapped_column(String(16), nullable=False)
    lesson_duration: Mapped[int] = mapped_column(nullable=False)
    speaking_priority: Mapped[int] = mapped_column(nullable=False)
    grammar_priority: Mapped[int] = mapped_column(nullable=False)
    profession_priority: Mapped[int] = mapped_column(nullable=False)

    lesson_runs = relationship("LessonRun", back_populates="user", cascade="all, delete-orphan")
    mistake_records = relationship("MistakeRecord", back_populates="user", cascade="all, delete-orphan")
    progress_snapshots = relationship("ProgressSnapshot", back_populates="user", cascade="all, delete-orphan")
    vocabulary_items = relationship("VocabularyItem", back_populates="user", cascade="all, delete-orphan")
    provider_preferences = relationship(
        "UserProviderPreference",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    speaking_attempts = relationship("SpeakingAttempt", back_populates="user", cascade="all, delete-orphan")
    pronunciation_attempts = relationship("PronunciationAttempt", back_populates="user", cascade="all, delete-orphan")
    writing_attempts = relationship("WritingAttempt", back_populates="user", cascade="all, delete-orphan")

from __future__ import annotations

from sqlalchemy import CheckConstraint, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GrammarTopic(Base):
    __tablename__ = "grammar_topics"
    __table_args__ = (
        CheckConstraint("mastery >= 0 AND mastery <= 100", name="ck_grammar_topics_mastery"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    mastery: Mapped[int] = mapped_column(nullable=False, default=0)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    checkpoints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


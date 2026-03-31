from __future__ import annotations

from sqlalchemy import JSON, Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import ProfessionDomain


lesson_template_profession_topics = Table(
    "lesson_template_profession_topics",
    Base.metadata,
    Column("lesson_template_id", String(64), ForeignKey("lesson_templates.id", ondelete="CASCADE"), primary_key=True),
    Column("profession_topic_id", String(64), ForeignKey("profession_topics.id", ondelete="CASCADE"), primary_key=True),
)


class ProfessionTopic(Base):
    __tablename__ = "profession_topics"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    domain: Mapped[ProfessionDomain] = mapped_column(
        enum_type(ProfessionDomain, "profession_domain_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    lesson_templates = relationship(
        "LessonTemplate",
        secondary=lesson_template_profession_topics,
        back_populates="profession_topics",
    )

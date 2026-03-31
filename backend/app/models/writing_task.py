from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WritingTask(Base):
    __tablename__ = "writing_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    brief: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str] = mapped_column(String(128), nullable=False)
    checklist: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    improved_version_preview: Mapped[str] = mapped_column(Text, nullable=False)


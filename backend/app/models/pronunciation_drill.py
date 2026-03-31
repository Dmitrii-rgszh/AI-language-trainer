from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PronunciationDrill(Base):
    __tablename__ = "pronunciation_drills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sound: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    focus: Mapped[str] = mapped_column(Text, nullable=False)
    phrases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)


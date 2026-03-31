from __future__ import annotations

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.blueprint import ProfessionDomain


class ProfessionTrack(Base):
    __tablename__ = "profession_tracks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[ProfessionDomain] = mapped_column(
        enum_type(ProfessionDomain, "profession_domain_enum"),
        nullable=False,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    lesson_focus: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


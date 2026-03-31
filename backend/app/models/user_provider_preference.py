from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.common import enum_type
from app.schemas.provider import ProviderType


class UserProviderPreference(Base):
    __tablename__ = "user_provider_preferences"

    user_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    provider_type: Mapped[ProviderType] = mapped_column(
        enum_type(ProviderType, "provider_type_enum"),
        primary_key=True,
    )
    selected_provider: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    user = relationship("UserProfile", back_populates="provider_preferences")

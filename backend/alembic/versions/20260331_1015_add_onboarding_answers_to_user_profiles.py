"""add onboarding answers to user profiles

Revision ID: 20260331_1015
Revises: 20260321_0030
Create Date: 2026-03-31 10:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_1015"
down_revision = "20260321_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("onboarding_answers", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "onboarding_answers")

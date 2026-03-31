"""add vocabulary source metadata

Revision ID: 20260321_0010
Revises: 20260320_2345
Create Date: 2026-03-21 00:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260321_0010"
down_revision = "20260320_2345"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column("source_module", sa.String(length=64), nullable=False, server_default="seed"),
    )
    op.add_column(
        "vocabulary_items",
        sa.Column("review_reason", sa.Text(), nullable=False, server_default="Core vocabulary practice"),
    )


def downgrade() -> None:
    op.drop_column("vocabulary_items", "review_reason")
    op.drop_column("vocabulary_items", "source_module")

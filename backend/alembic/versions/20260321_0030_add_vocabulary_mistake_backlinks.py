"""add vocabulary mistake backlinks

Revision ID: 20260321_0030
Revises: 20260321_0010
Create Date: 2026-03-21 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260321_0030"
down_revision = "20260321_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vocabulary_items",
        sa.Column("linked_mistake_subtype", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "vocabulary_items",
        sa.Column("linked_mistake_title", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_vocabulary_items_linked_mistake_subtype"),
        "vocabulary_items",
        ["linked_mistake_subtype"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_vocabulary_items_linked_mistake_subtype"), table_name="vocabulary_items")
    op.drop_column("vocabulary_items", "linked_mistake_title")
    op.drop_column("vocabulary_items", "linked_mistake_subtype")

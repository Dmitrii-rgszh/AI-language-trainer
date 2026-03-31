"""add pronunciation attempts

Revision ID: 20260320_2315
Revises: 20260320_2235
Create Date: 2026-03-20 23:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_2315"
down_revision = "20260320_2235"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pronunciation_attempts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("drill_id", sa.String(length=64), nullable=True),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("sound_focus", sa.String(length=128), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("weakest_words", sa.JSON(), nullable=False),
        sa.Column("focus_issues", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["drill_id"], ["pronunciation_drills.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pronunciation_attempts_drill_id"), "pronunciation_attempts", ["drill_id"], unique=False)
    op.create_index(op.f("ix_pronunciation_attempts_sound_focus"), "pronunciation_attempts", ["sound_focus"], unique=False)
    op.create_index(op.f("ix_pronunciation_attempts_user_id"), "pronunciation_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pronunciation_attempts_user_id"), table_name="pronunciation_attempts")
    op.drop_index(op.f("ix_pronunciation_attempts_sound_focus"), table_name="pronunciation_attempts")
    op.drop_index(op.f("ix_pronunciation_attempts_drill_id"), table_name="pronunciation_attempts")
    op.drop_table("pronunciation_attempts")

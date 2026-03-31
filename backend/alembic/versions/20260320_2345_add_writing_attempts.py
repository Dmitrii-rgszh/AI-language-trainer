"""add writing attempts

Revision ID: 20260320_2345
Revises: 20260320_2315
Create Date: 2026-03-20 23:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260320_2345"
down_revision = "20260320_2315"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "writing_attempts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("task_id", sa.String(length=64), nullable=False),
        sa.Column("draft", sa.Text(), nullable=False),
        sa.Column("feedback_summary", sa.Text(), nullable=False),
        sa.Column("feedback_source", sa.String(length=16), nullable=False),
        sa.Column("voice_text", sa.Text(), nullable=False),
        sa.Column("voice_language", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["writing_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_writing_attempts_task_id"), "writing_attempts", ["task_id"], unique=False)
    op.create_index(op.f("ix_writing_attempts_user_id"), "writing_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_writing_attempts_user_id"), table_name="writing_attempts")
    op.drop_index(op.f("ix_writing_attempts_task_id"), table_name="writing_attempts")
    op.drop_table("writing_attempts")

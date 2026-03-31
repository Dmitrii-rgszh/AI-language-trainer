"""add speaking attempts

Revision ID: 20260320_2235
Revises: 20260320_2005
Create Date: 2026-03-20 22:35:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260320_2235"
down_revision: str | None = "20260320_2005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "speaking_attempts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("scenario_id", sa.String(length=64), nullable=False),
        sa.Column("input_mode", sa.String(length=16), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("feedback_summary", sa.Text(), nullable=False),
        sa.Column("feedback_source", sa.String(length=16), nullable=False),
        sa.Column("voice_text", sa.Text(), nullable=False),
        sa.Column("voice_language", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["scenario_id"], ["speaking_scenarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_speaking_attempts_input_mode"), "speaking_attempts", ["input_mode"], unique=False)
    op.create_index(op.f("ix_speaking_attempts_scenario_id"), "speaking_attempts", ["scenario_id"], unique=False)
    op.create_index(op.f("ix_speaking_attempts_user_id"), "speaking_attempts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_speaking_attempts_user_id"), table_name="speaking_attempts")
    op.drop_index(op.f("ix_speaking_attempts_scenario_id"), table_name="speaking_attempts")
    op.drop_index(op.f("ix_speaking_attempts_input_mode"), table_name="speaking_attempts")
    op.drop_table("speaking_attempts")


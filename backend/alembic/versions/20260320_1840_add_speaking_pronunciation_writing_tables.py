"""add speaking pronunciation writing tables

Revision ID: 20260320_1840
Revises: 20260320_1810
Create Date: 2026-03-20 18:40:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_1840"
down_revision = "20260320_1810"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "speaking_scenarios",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("feedback_hint", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_speaking_scenarios_mode", "speaking_scenarios", ["mode"], unique=False)

    op.create_table(
        "pronunciation_drills",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("sound", sa.String(length=64), nullable=False),
        sa.Column("focus", sa.Text(), nullable=False),
        sa.Column("phrases", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pronunciation_drills_sound", "pronunciation_drills", ["sound"], unique=False)

    op.create_table(
        "writing_tasks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=128), nullable=False),
        sa.Column("checklist", sa.JSON(), nullable=False),
        sa.Column("improved_version_preview", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("writing_tasks")
    op.drop_index("ix_pronunciation_drills_sound", table_name="pronunciation_drills")
    op.drop_table("pronunciation_drills")
    op.drop_index("ix_speaking_scenarios_mode", table_name="speaking_scenarios")
    op.drop_table("speaking_scenarios")


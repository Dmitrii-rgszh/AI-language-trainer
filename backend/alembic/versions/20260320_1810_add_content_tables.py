"""add content tables

Revision ID: 20260320_1810
Revises: 20260320_1645
Create Date: 2026-03-20 18:10:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_1810"
down_revision = "20260320_1645"
branch_labels = None
depends_on = None


profession_domain_enum = sa.Enum(
    "insurance",
    "banking",
    "trainer_skills",
    "ai_business",
    "regulation",
    "cross_cultural",
    name="profession_domain_enum",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "grammar_topics",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("mastery", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("checkpoints", sa.JSON(), nullable=False),
        sa.CheckConstraint("mastery >= 0 AND mastery <= 100", name="ck_grammar_topics_mastery"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_grammar_topics_level", "grammar_topics", ["level"], unique=False)

    op.create_table(
        "profession_tracks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("domain", profession_domain_enum, nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("lesson_focus", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profession_tracks_domain", "profession_tracks", ["domain"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_profession_tracks_domain", table_name="profession_tracks")
    op.drop_table("profession_tracks")

    op.drop_index("ix_grammar_topics_level", table_name="grammar_topics")
    op.drop_table("grammar_topics")


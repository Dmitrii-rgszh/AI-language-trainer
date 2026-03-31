"""add provider preferences

Revision ID: 20260320_2005
Revises: 20260320_1840
Create Date: 2026-03-20 20:05:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_2005"
down_revision = "20260320_1840"
branch_labels = None
depends_on = None


provider_type_enum = sa.Enum(
    "llm",
    "stt",
    "tts",
    "scoring",
    name="provider_type_enum",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "user_provider_preferences",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("provider_type", provider_type_enum, nullable=False),
        sa.Column("selected_provider", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "provider_type"),
    )


def downgrade() -> None:
    op.drop_table("user_provider_preferences")
    provider_type_enum.drop(op.get_bind(), checkfirst=True)

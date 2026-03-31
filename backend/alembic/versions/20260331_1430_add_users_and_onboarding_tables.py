"""add users and onboarding tables

Revision ID: 20260331_1430
Revises: 20260331_1015
Create Date: 2026-03-31 14:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_1430"
down_revision = "20260331_1015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("login"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_login"), "users", ["login"], unique=True)

    op.create_table(
        "user_onboarding",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_onboarding_user_id"), "user_onboarding", ["user_id"], unique=True)

    op.execute(
        """
        INSERT INTO users (id, login, email, created_at, updated_at)
        SELECT
            user_profiles.id,
            CASE
                WHEN user_profiles.id = 'user-local-1' THEN 'learner'
                ELSE user_profiles.id
            END,
            CASE
                WHEN user_profiles.id = 'user-local-1' THEN 'learner@local.test'
                ELSE user_profiles.id || '@local.test'
            END,
            user_profiles.created_at,
            user_profiles.updated_at
        FROM user_profiles
        WHERE NOT EXISTS (
            SELECT 1
            FROM users
            WHERE users.id = user_profiles.id
        )
        """
    )

    op.execute(
        """
        INSERT INTO user_onboarding (id, user_id, answers, completed_at, created_at, updated_at)
        SELECT
            'onboarding-' || user_profiles.id,
            user_profiles.id,
            user_profiles.onboarding_answers,
            user_profiles.updated_at,
            user_profiles.created_at,
            user_profiles.updated_at
        FROM user_profiles
        WHERE NOT EXISTS (
            SELECT 1
            FROM user_onboarding
            WHERE user_onboarding.user_id = user_profiles.id
        )
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_onboarding_user_id"), table_name="user_onboarding")
    op.drop_table("user_onboarding")

    op.drop_index(op.f("ix_users_login"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

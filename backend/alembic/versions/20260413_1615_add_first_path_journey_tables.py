"""add first path journey tables

Revision ID: 20260413_1615
Revises: 20260331_1430
Create Date: 2026-04-13 16:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_1615"
down_revision = "20260331_1430"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "onboarding_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("proof_lesson_handoff", sa.JSON(), nullable=False),
        sa.Column("account_draft", sa.JSON(), nullable=False),
        sa.Column("profile_draft", sa.JSON(), nullable=False),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("current_step >= 0", name="ck_onboarding_sessions_current_step"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_onboarding_sessions_user_id"), "onboarding_sessions", ["user_id"], unique=False)

    op.create_table(
        "learner_journey_states",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("preferred_mode", sa.String(length=32), nullable=False),
        sa.Column("diagnostic_readiness", sa.String(length=32), nullable=False),
        sa.Column("time_budget_minutes", sa.Integer(), nullable=False),
        sa.Column("current_focus_area", sa.String(length=64), nullable=False),
        sa.Column("current_strategy_summary", sa.Text(), nullable=False),
        sa.Column("next_best_action", sa.Text(), nullable=False),
        sa.Column("last_daily_plan_id", sa.String(length=64), nullable=True),
        sa.Column("proof_lesson_handoff", sa.JSON(), nullable=False),
        sa.Column("strategy_snapshot", sa.JSON(), nullable=False),
        sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "time_budget_minutes >= 10 AND time_budget_minutes <= 120",
            name="ck_learner_journey_state_time_budget",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "daily_loop_plans",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("plan_date_key", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("session_kind", sa.String(length=32), nullable=False),
        sa.Column("focus_area", sa.String(length=64), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("why_this_now", sa.Text(), nullable=False),
        sa.Column("next_step_hint", sa.Text(), nullable=False),
        sa.Column("preferred_mode", sa.String(length=32), nullable=False),
        sa.Column("time_budget_minutes", sa.Integer(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("recommended_lesson_type", sa.String(length=32), nullable=False),
        sa.Column("recommended_lesson_title", sa.String(length=255), nullable=False),
        sa.Column("lesson_run_id", sa.String(length=64), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("completion_summary", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "time_budget_minutes >= 10 AND time_budget_minutes <= 120",
            name="ck_daily_loop_plans_time_budget",
        ),
        sa.CheckConstraint(
            "estimated_minutes >= 10 AND estimated_minutes <= 120",
            name="ck_daily_loop_plans_estimated_minutes",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "plan_date_key", name="uq_daily_loop_plans_user_date"),
    )
    op.create_index(op.f("ix_daily_loop_plans_user_id"), "daily_loop_plans", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_loop_plans_user_id"), table_name="daily_loop_plans")
    op.drop_table("daily_loop_plans")
    op.drop_table("learner_journey_states")
    op.drop_index(op.f("ix_onboarding_sessions_user_id"), table_name="onboarding_sessions")
    op.drop_table("onboarding_sessions")

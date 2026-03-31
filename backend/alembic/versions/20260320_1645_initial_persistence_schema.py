"""initial persistence schema

Revision ID: 20260320_1645
Revises: 
Create Date: 2026-03-20 16:45:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260320_1645"
down_revision = None
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

lesson_type_enum = sa.Enum(
    "core",
    "grammar",
    "speaking",
    "pronunciation",
    "writing",
    "professional",
    "mixed",
    "recovery",
    name="lesson_type_enum",
    native_enum=False,
    create_constraint=True,
)

feedback_mode_enum = sa.Enum(
    "immediate",
    "after_block",
    "critical_only",
    name="feedback_mode_enum",
    native_enum=False,
    create_constraint=True,
)

lesson_run_status_enum = sa.Enum(
    "planned",
    "in_progress",
    "completed",
    "skipped",
    name="lesson_run_status_enum",
    native_enum=False,
    create_constraint=True,
)

block_run_status_enum = sa.Enum(
    "pending",
    "active",
    "completed",
    "skipped",
    name="block_run_status_enum",
    native_enum=False,
    create_constraint=True,
)

user_response_type_enum = sa.Enum(
    "none",
    "text",
    "voice",
    "multiple_choice",
    name="user_response_type_enum",
    native_enum=False,
    create_constraint=True,
)

mistake_category_enum = sa.Enum(
    "grammar",
    "pronunciation",
    "vocabulary",
    "speaking",
    "writing",
    "profession",
    name="mistake_category_enum",
    native_enum=False,
    create_constraint=True,
)

mistake_severity_enum = sa.Enum(
    "low",
    "medium",
    "high",
    name="mistake_severity_enum",
    native_enum=False,
    create_constraint=True,
)

skill_area_enum = sa.Enum(
    "grammar",
    "speaking",
    "listening",
    "pronunciation",
    "writing",
    "vocabulary",
    "interview",
    "profession_english",
    "insurance_eu",
    "banking_eu",
    "regulation_eu",
    "ai_for_business",
    name="skill_area_enum",
    native_enum=False,
    create_constraint=True,
)

vocabulary_status_enum = sa.Enum(
    "new",
    "active",
    "mastered",
    name="vocabulary_status_enum",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    op.create_table(
        "profession_topics",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("domain", profession_domain_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("examples", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("native_language", sa.String(length=32), nullable=False),
        sa.Column("current_level", sa.String(length=16), nullable=False),
        sa.Column("target_level", sa.String(length=16), nullable=False),
        sa.Column("profession_track", profession_domain_enum, nullable=False),
        sa.Column("preferred_ui_language", sa.String(length=16), nullable=False),
        sa.Column("preferred_explanation_language", sa.String(length=16), nullable=False),
        sa.Column("lesson_duration", sa.Integer(), nullable=False),
        sa.Column("speaking_priority", sa.Integer(), nullable=False),
        sa.Column("grammar_priority", sa.Integer(), nullable=False),
        sa.Column("profession_priority", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("grammar_priority >= 1 AND grammar_priority <= 10", name="ck_user_profiles_grammar_priority"),
        sa.CheckConstraint("lesson_duration >= 10 AND lesson_duration <= 90", name="ck_user_profiles_lesson_duration"),
        sa.CheckConstraint(
            "profession_priority >= 1 AND profession_priority <= 10",
            name="ck_user_profiles_profession_priority",
        ),
        sa.CheckConstraint(
            "speaking_priority >= 1 AND speaking_priority <= 10",
            name="ck_user_profiles_speaking_priority",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lesson_templates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("lesson_type", lesson_type_enum, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("estimated_duration", sa.Integer(), nullable=False),
        sa.Column("enabled_tracks", sa.JSON(), nullable=False),
        sa.Column("generation_rules", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "estimated_duration >= 5 AND estimated_duration <= 120",
            name="ck_lesson_templates_estimated_duration",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lesson_template_profession_topics",
        sa.Column("lesson_template_id", sa.String(length=64), nullable=False),
        sa.Column("profession_topic_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["lesson_template_id"], ["lesson_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profession_topic_id"], ["profession_topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("lesson_template_id", "profession_topic_id"),
    )

    op.create_table(
        "lesson_blocks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("lesson_template_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("feedback_mode", feedback_mode_enum, nullable=False),
        sa.Column("depends_on_block_ids", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.CheckConstraint("estimated_minutes >= 1 AND estimated_minutes <= 60", name="ck_lesson_blocks_estimated_minutes"),
        sa.CheckConstraint("position >= 0", name="ck_lesson_blocks_position"),
        sa.ForeignKeyConstraint(["lesson_template_id"], ["lesson_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesson_blocks_block_type", "lesson_blocks", ["block_type"], unique=False)
    op.create_index("ix_lesson_blocks_lesson_template_id", "lesson_blocks", ["lesson_template_id"], unique=False)

    op.create_table(
        "lesson_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("template_id", sa.String(length=64), nullable=False),
        sa.Column("status", lesson_run_status_enum, nullable=False),
        sa.Column("recommended_by", sa.String(length=128), nullable=False),
        sa.Column("weak_spot_ids", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_lesson_runs_score"),
        sa.ForeignKeyConstraint(["template_id"], ["lesson_templates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesson_runs_status", "lesson_runs", ["status"], unique=False)
    op.create_index("ix_lesson_runs_template_id", "lesson_runs", ["template_id"], unique=False)
    op.create_index("ix_lesson_runs_user_id", "lesson_runs", ["user_id"], unique=False)

    op.create_table(
        "progress_snapshots",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("lesson_run_id", sa.String(length=64), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("daily_goal_minutes", sa.Integer(), nullable=False),
        sa.Column("minutes_completed_today", sa.Integer(), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.CheckConstraint("daily_goal_minutes >= 0 AND daily_goal_minutes <= 180", name="ck_progress_daily_goal"),
        sa.CheckConstraint(
            "minutes_completed_today >= 0 AND minutes_completed_today <= 180",
            name="ck_progress_minutes_completed",
        ),
        sa.CheckConstraint("streak >= 0", name="ck_progress_streak"),
        sa.ForeignKeyConstraint(["lesson_run_id"], ["lesson_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_progress_snapshots_lesson_run_id", "progress_snapshots", ["lesson_run_id"], unique=False)
    op.create_index("ix_progress_snapshots_snapshot_date", "progress_snapshots", ["snapshot_date"], unique=False)
    op.create_index("ix_progress_snapshots_user_id", "progress_snapshots", ["user_id"], unique=False)

    op.create_table(
        "vocabulary_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("word", sa.String(length=255), nullable=False),
        sa.Column("translation", sa.String(length=255), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("learned_status", vocabulary_status_enum, nullable=False),
        sa.Column("repetition_stage", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("repetition_stage >= 0 AND repetition_stage <= 10", name="ck_vocabulary_repetition_stage"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vocabulary_items_category", "vocabulary_items", ["category"], unique=False)
    op.create_index("ix_vocabulary_items_learned_status", "vocabulary_items", ["learned_status"], unique=False)
    op.create_index("ix_vocabulary_items_user_id", "vocabulary_items", ["user_id"], unique=False)
    op.create_index("ix_vocabulary_items_word", "vocabulary_items", ["word"], unique=False)

    op.create_table(
        "lesson_block_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("lesson_run_id", sa.String(length=64), nullable=False),
        sa.Column("block_id", sa.String(length=64), nullable=False),
        sa.Column("status", block_run_status_enum, nullable=False),
        sa.Column("user_response_type", user_response_type_enum, nullable=False),
        sa.Column("user_response", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("feedback_summary", sa.Text(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_lesson_block_runs_score"),
        sa.ForeignKeyConstraint(["block_id"], ["lesson_blocks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["lesson_run_id"], ["lesson_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lesson_block_runs_block_id", "lesson_block_runs", ["block_id"], unique=False)
    op.create_index("ix_lesson_block_runs_lesson_run_id", "lesson_block_runs", ["lesson_run_id"], unique=False)
    op.create_index("ix_lesson_block_runs_status", "lesson_block_runs", ["status"], unique=False)

    op.create_table(
        "mistake_records",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("category", mistake_category_enum, nullable=False),
        sa.Column("subtype", sa.String(length=128), nullable=False),
        sa.Column("source_module", sa.String(length=64), nullable=False),
        sa.Column("source_block_run_id", sa.String(length=64), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("corrected_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("severity", mistake_severity_enum, nullable=False),
        sa.Column("repetition_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("repetition_count >= 1", name="ck_mistake_records_repetition_count"),
        sa.ForeignKeyConstraint(["source_block_run_id"], ["lesson_block_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mistake_records_category", "mistake_records", ["category"], unique=False)
    op.create_index("ix_mistake_records_source_block_run_id", "mistake_records", ["source_block_run_id"], unique=False)
    op.create_index("ix_mistake_records_source_module", "mistake_records", ["source_module"], unique=False)
    op.create_index("ix_mistake_records_subtype", "mistake_records", ["subtype"], unique=False)
    op.create_index("ix_mistake_records_user_id", "mistake_records", ["user_id"], unique=False)

    op.create_table(
        "progress_skill_scores",
        sa.Column("progress_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("area", skill_area_enum, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_progress_skill_scores_confidence"),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_progress_skill_scores_score"),
        sa.ForeignKeyConstraint(["progress_snapshot_id"], ["progress_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("progress_snapshot_id", "area"),
    )


def downgrade() -> None:
    op.drop_table("progress_skill_scores")

    op.drop_index("ix_mistake_records_user_id", table_name="mistake_records")
    op.drop_index("ix_mistake_records_subtype", table_name="mistake_records")
    op.drop_index("ix_mistake_records_source_module", table_name="mistake_records")
    op.drop_index("ix_mistake_records_source_block_run_id", table_name="mistake_records")
    op.drop_index("ix_mistake_records_category", table_name="mistake_records")
    op.drop_table("mistake_records")

    op.drop_index("ix_lesson_block_runs_status", table_name="lesson_block_runs")
    op.drop_index("ix_lesson_block_runs_lesson_run_id", table_name="lesson_block_runs")
    op.drop_index("ix_lesson_block_runs_block_id", table_name="lesson_block_runs")
    op.drop_table("lesson_block_runs")

    op.drop_index("ix_vocabulary_items_word", table_name="vocabulary_items")
    op.drop_index("ix_vocabulary_items_user_id", table_name="vocabulary_items")
    op.drop_index("ix_vocabulary_items_learned_status", table_name="vocabulary_items")
    op.drop_index("ix_vocabulary_items_category", table_name="vocabulary_items")
    op.drop_table("vocabulary_items")

    op.drop_index("ix_progress_snapshots_user_id", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_snapshot_date", table_name="progress_snapshots")
    op.drop_index("ix_progress_snapshots_lesson_run_id", table_name="progress_snapshots")
    op.drop_table("progress_snapshots")

    op.drop_index("ix_lesson_runs_user_id", table_name="lesson_runs")
    op.drop_index("ix_lesson_runs_template_id", table_name="lesson_runs")
    op.drop_index("ix_lesson_runs_status", table_name="lesson_runs")
    op.drop_table("lesson_runs")

    op.drop_index("ix_lesson_blocks_lesson_template_id", table_name="lesson_blocks")
    op.drop_index("ix_lesson_blocks_block_type", table_name="lesson_blocks")
    op.drop_table("lesson_blocks")

    op.drop_table("lesson_template_profession_topics")
    op.drop_table("lesson_templates")
    op.drop_table("user_profiles")
    op.drop_table("profession_topics")

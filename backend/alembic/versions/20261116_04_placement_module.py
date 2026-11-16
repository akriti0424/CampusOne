"""placement preparation module

Revision ID: 20261116_04
Revises: 20260725_03
"""

from alembic import op
import sqlalchemy as sa


revision = "20261116_04"
down_revision = "20260725_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "placement_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pillar", sa.String(50), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("question_format", sa.String(20), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("sample_input", sa.Text(), nullable=True),
        sa.Column("sample_output", sa.Text(), nullable=True),
        sa.Column("hints", sa.JSON(), nullable=True),
        sa.Column("optimal_approach", sa.Text(), nullable=True),
        sa.Column("time_complexity", sa.String(40), nullable=True),
        sa.Column("space_complexity", sa.String(40), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("company_tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_placement_questions_pillar", "placement_questions", ["pillar"])
    op.create_index("ix_placement_questions_topic", "placement_questions", ["topic"])
    op.create_index("ix_placement_questions_difficulty", "placement_questions", ["difficulty"])
    op.create_table(
        "placement_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("placement_questions.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="unsolved"),
        sa.Column("bookmarked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "question_id", name="uq_placement_progress_user_question"),
    )
    op.create_table(
        "placement_tests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("company", sa.String(80), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("negative_marking", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("section_switching", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "placement_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("test_id", sa.Integer(), sa.ForeignKey("placement_tests.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wrong_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_stats", sa.JSON(), nullable=False),
    )
    op.create_table(
        "placement_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("placement_attempts.id"), nullable=False),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("placement_questions.id"), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("time_spent_seconds", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("placement_answers")
    op.drop_table("placement_attempts")
    op.drop_table("placement_tests")
    op.drop_table("placement_progress")
    op.drop_index("ix_placement_questions_difficulty", table_name="placement_questions")
    op.drop_index("ix_placement_questions_topic", table_name="placement_questions")
    op.drop_index("ix_placement_questions_pillar", table_name="placement_questions")
    op.drop_table("placement_questions")

"""add top-question flag to placement questions

Revision ID: 20261116_05
Revises: 20261116_04
"""

from alembic import op
import sqlalchemy as sa


revision = "20261116_05"
down_revision = "20261116_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "placement_questions",
        sa.Column("is_top_question", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("placement_questions", "is_top_question")

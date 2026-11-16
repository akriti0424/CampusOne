"""separate quiz questions from top questions

Revision ID: 20261116_07
Revises: 20261116_06
"""

from alembic import op
import sqlalchemy as sa


revision = "20261116_07"
down_revision = "20261116_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "placement_questions",
        sa.Column("is_quiz_question", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("placement_questions", "is_quiz_question")

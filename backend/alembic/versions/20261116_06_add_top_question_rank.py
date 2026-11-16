"""add stable rank for per-topic top questions

Revision ID: 20261116_06
Revises: 20261116_05
"""

from alembic import op
import sqlalchemy as sa


revision = "20261116_06"
down_revision = "20261116_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("placement_questions", sa.Column("top_rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("placement_questions", "top_rank")

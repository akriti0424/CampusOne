"""add email verification fields

Revision ID: 20260725_02
Revises: 20260725_01
Create Date: 2026-07-25 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260725_02"
down_revision = "20260725_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("email_otp_hash", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("email_otp_expires_at", sa.DateTime(timezone=True), nullable=True))
    # Accounts that existed before verification was introduced remain usable.
    op.execute("UPDATE users SET is_verified = true")


def downgrade() -> None:
    op.drop_column("users", "email_otp_expires_at")
    op.drop_column("users", "email_otp_hash")
    op.drop_column("users", "is_verified")

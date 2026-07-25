"""store account signups outside users until email verification

Revision ID: 20260725_03
Revises: 20260725_02
Create Date: 2026-07-25 00:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260725_03"
down_revision = "20260725_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_registrations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("scholar_id", sa.String(length=30), nullable=False),
        sa.Column("branch", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("email_otp_hash", sa.String(length=255), nullable=False),
        sa.Column("email_otp_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scholar_id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_pending_registrations_id"), "pending_registrations", ["id"], unique=False)
    op.create_index(op.f("ix_pending_registrations_scholar_id"), "pending_registrations", ["scholar_id"], unique=False)
    op.create_index(op.f("ix_pending_registrations_email"), "pending_registrations", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pending_registrations_email"), table_name="pending_registrations")
    op.drop_index(op.f("ix_pending_registrations_scholar_id"), table_name="pending_registrations")
    op.drop_index(op.f("ix_pending_registrations_id"), table_name="pending_registrations")
    op.drop_table("pending_registrations")

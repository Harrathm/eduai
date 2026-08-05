"""Add scheduled_tier_change to abonnements

Revision ID: 0005_scheduled_tier_change
Revises: 7804b0ec91bf
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_scheduled_tier_change"
down_revision = "7804b0ec91bf"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("abonnements", sa.Column("scheduled_tier", sa.String(20), nullable=True))
    op.add_column("abonnements", sa.Column("scheduled_effective_date", sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column("abonnements", "scheduled_effective_date")
    op.drop_column("abonnements", "scheduled_tier")

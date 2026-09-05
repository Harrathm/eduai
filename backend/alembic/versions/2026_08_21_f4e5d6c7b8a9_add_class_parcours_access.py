"""Add class_parcours_access table

Revision ID: f4e5d6c7b8a9
Revises: a1b2c3d4e5f6
Create Date: 2026-08-21 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "f4e5d6c7b8a9"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "class_parcours_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("teacher_classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parcours_id", sa.Integer(), sa.ForeignKey("parcours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_cpa_class_parcours", "class_parcours_access", ["class_id", "parcours_id"], unique=True)
    op.create_index("ix_cpa_class_id", "class_parcours_access", ["class_id"])
    op.create_index("ix_cpa_parcours_id", "class_parcours_access", ["parcours_id"])


def downgrade() -> None:
    op.drop_table("class_parcours_access")

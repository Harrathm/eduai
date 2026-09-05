"""add content_promotions.element_promoted_id for snapshot-copy promotions

Revision ID: c9d0e1f2a3b4
Revises: b4c8e1f7a2d5
Create Date: 2026-08-23

Links the promoted global copy back to its source element
(snapshot-copy-only model for promote-global).
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c9d0e1f2a3b4"
down_revision = "b4c8e1f7a2d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_promotions",
        sa.Column(
            "element_promoted_id",
            sa.Integer(),
            sa.ForeignKey("elements_pedagogiques.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_content_promotions_promoted",
        "content_promotions",
        ["element_promoted_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_content_promotions_promoted", table_name="content_promotions")
    op.drop_column("content_promotions", "element_promoted_id")

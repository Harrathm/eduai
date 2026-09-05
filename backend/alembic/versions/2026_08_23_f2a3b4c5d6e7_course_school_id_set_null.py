"""Fix #3 — Course.school_id ON DELETE SET NULL (préservation bibliothèque globale)

La FK Course.school_id utilisait ON DELETE CASCADE, ce qui supprimait les
cours promus en bibliothèque globale (owner_type="eduai_catalog") lors de la
suppression d'un tenant école. Changement vers SET NULL + nullable=True pour
que les cours survivent à la résiliation du tenant.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-08-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Supprimer l'ancienne FK CASCADE
    op.drop_constraint("courses_school_id_fkey", "courses", type_="foreignkey")
    # Recréer avec SET NULL + nullable
    op.alter_column(
        "courses", "school_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_courses_school_id_schools",
        "courses", "schools",
        ["school_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_courses_school_id_schools", "courses", type_="foreignkey")
    op.alter_column(
        "courses", "school_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "courses_school_id_fkey",
        "courses", "schools",
        ["school_id"], ["id"],
        ondelete="CASCADE",
    )

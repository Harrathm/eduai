"""course.author_id ON DELETE CASCADE -> SET NULL (institutional ownership)

Supprimer un enseignant ne doit plus supprimer ses cours :
la FK passe en SET NULL et la colonne devient nullable.
ElementPedagogique.auteur_id est déjà en SET NULL côté modèle.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-08-23
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None

CONSTRAINT = "courses_author_id_fkey"


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT, "courses", type_="foreignkey")
    op.create_foreign_key(
        CONSTRAINT,
        source_table="courses",
        referent_table="users",
        local_cols=["author_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )
    op.alter_column("courses", "author_id", existing_type="INTEGER", nullable=True)


def downgrade() -> None:
    # Re-attach orphaned courses to a placeholder is out of scope;
    # this downgrade only restores the constraint shape and requires no NULL author_id.
    op.execute('DELETE FROM courses WHERE author_id IS NULL')
    op.alter_column("courses", "author_id", existing_type="INTEGER", nullable=False)
    op.drop_constraint(CONSTRAINT, "courses", type_="foreignkey")
    op.create_foreign_key(
        CONSTRAINT,
        source_table="courses",
        referent_table="users",
        local_cols=["author_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

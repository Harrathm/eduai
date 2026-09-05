"""users.invitation_code — code d'invitation parental des élèves (M2 FIX)

La liaison parent-enfant par simple email (POST /parents/me/enfants/lier)
constituait un IDOR: tout parent pouvait rattacher n'importe quel élève de
son école. Le code d'invitation (6 caractères, unique, nullable — généré à la
création de l'élève) devient la preuve de possession exigée par l'endpoint.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-08-23
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("invitation_code", sa.String(length=12), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_invitation_code", "users", ["invitation_code"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_users_invitation_code", "users", type_="unique")
    op.drop_column("users", "invitation_code")

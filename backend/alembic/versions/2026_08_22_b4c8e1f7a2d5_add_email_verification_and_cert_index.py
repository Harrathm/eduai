"""Add email verification fields + certificate_number index

Revision ID: b4c8e1f7a2d5
Revises: f4e5d6c7b8a9
Create Date: 2026-08-22 10:00:00.000000

FIX #6 : users.email_verified + users.email_verification_token
FIX #11 : index explicite sur certificates.certificate_number
          (la contrainte UNIQUE existe déjà depuis 0001_initial_full_schema ;
           l'index nommé garantit le plan d'exécution et l'intention modèle)
"""
from alembic import op
import sqlalchemy as sa

revision = "b4c8e1f7a2d5"
down_revision = "f4e5d6c7b8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_token", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_email_verification_token", "users", ["email_verification_token"]
    )
    op.create_index(
        "ix_certificates_certificate_number",
        "certificates",
        ["certificate_number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_certificates_certificate_number", table_name="certificates")
    op.drop_constraint("uq_users_email_verification_token", "users", type_="unique")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")

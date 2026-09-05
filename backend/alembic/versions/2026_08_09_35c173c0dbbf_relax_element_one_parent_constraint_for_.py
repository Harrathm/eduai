"""relax_element_one_parent_constraint_for_global

Revision ID: 35c173c0dbbf
Revises: 0006_float_to_numeric_monetary
Create Date: 2026-08-09 09:58:36.068333

"""
from typing import Sequence, Union
from alembic import op

revision: str = '35c173c0dbbf'
down_revision: Union[str, None] = '0006_float_to_numeric_monetary'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE elements_pedagogiques DROP CONSTRAINT IF EXISTS ck_element_one_parent")
    op.execute(
        "ALTER TABLE elements_pedagogiques ADD CONSTRAINT ck_element_one_parent "
        "CHECK (est_global = true OR ((lecon_id IS NOT NULL AND paragraphe_id IS NULL) "
        "OR (lecon_id IS NULL AND paragraphe_id IS NOT NULL)))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE elements_pedagogiques DROP CONSTRAINT IF EXISTS ck_element_one_parent")
    op.execute(
        "ALTER TABLE elements_pedagogiques ADD CONSTRAINT ck_element_one_parent "
        "CHECK ((lecon_id IS NOT NULL AND paragraphe_id IS NULL) "
        "OR (lecon_id IS NULL AND paragraphe_id IS NOT NULL))"
    )

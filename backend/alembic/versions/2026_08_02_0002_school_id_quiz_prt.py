"""add school_id to quizzes and password_reset_tokens

Revision ID: 0002_school_id_quiz_prt
Revises: 0001_initial
Create Date: 2026-08-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_school_id_quiz_prt'
down_revision: Union[str, None] = '0001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- quizzes: add school_id ---
    op.add_column('quizzes', sa.Column('school_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_quizzes_school_id',
        'quizzes', 'schools',
        ['school_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_index('ix_quizzes_school_id', 'quizzes', ['school_id'])

    # Backfill quizzes.school_id from lessons → modules → courses
    op.execute("""
        UPDATE quizzes q
        SET school_id = c.school_id
        FROM lessons l
        JOIN modules m ON l.module_id = m.id
        JOIN courses c ON m.course_id = c.id
        WHERE q.lesson_id = l.id
          AND q.school_id IS NULL
          AND c.school_id IS NOT NULL
    """)

    # --- password_reset_tokens: add school_id ---
    op.add_column('password_reset_tokens', sa.Column('school_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_password_reset_tokens_school_id',
        'password_reset_tokens', 'schools',
        ['school_id'], ['id'],
        ondelete='CASCADE',
    )
    op.create_index('ix_password_reset_school_id', 'password_reset_tokens', ['school_id'])

    # Backfill password_reset_tokens.school_id from users
    op.execute("""
        UPDATE password_reset_tokens prt
        SET school_id = u.school_id
        FROM users u
        WHERE prt.user_id = u.id
          AND prt.school_id IS NULL
    """)


def downgrade() -> None:
    op.drop_index('ix_password_reset_school_id', table_name='password_reset_tokens')
    op.drop_constraint('fk_password_reset_tokens_school_id', 'password_reset_tokens', type_='foreignkey')
    op.drop_column('password_reset_tokens', 'school_id')

    op.drop_index('ix_quizzes_school_id', table_name='quizzes')
    op.drop_constraint('fk_quizzes_school_id', 'quizzes', type_='foreignkey')
    op.drop_column('quizzes', 'school_id')

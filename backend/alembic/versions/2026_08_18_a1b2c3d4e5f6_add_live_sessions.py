"""add_live_sessions

Revision ID: a1b2c3d4e5f6
Revises: 35c173c0dbbf
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '35c173c0dbbf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'live_sessions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('teacher_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.Integer, sa.ForeignKey('teacher_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer, sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('scheduled_at', sa.DateTime, nullable=False),
        sa.Column('duration_minutes', sa.Integer, server_default='60'),
        sa.Column('status', sa.String(20), server_default='upcoming'),
        sa.Column('meeting_url', sa.String(500)),
        sa.Column('meeting_token', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_ls_teacher_id', 'live_sessions', ['teacher_id'])
    op.create_index('ix_ls_class_id', 'live_sessions', ['class_id'])
    op.create_index('ix_ls_school_id', 'live_sessions', ['school_id'])
    op.create_index('ix_ls_scheduled_at', 'live_sessions', ['scheduled_at'])

    op.create_table(
        'live_attendance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('live_session_id', sa.Integer, sa.ForeignKey('live_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('joined_at', sa.DateTime),
        sa.Column('left_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('is_active', sa.Boolean, server_default='false'),
    )
    op.create_index('ix_la_session_student', 'live_attendance', ['live_session_id', 'student_id'], unique=True)
    op.create_index('ix_la_session_id', 'live_attendance', ['live_session_id'])
    op.create_index('ix_la_student_id', 'live_attendance', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_la_student_id', table_name='live_attendance')
    op.drop_index('ix_la_session_id', table_name='live_attendance')
    op.drop_index('ix_la_session_student', table_name='live_attendance')
    op.drop_table('live_attendance')

    op.drop_index('ix_ls_scheduled_at', table_name='live_sessions')
    op.drop_index('ix_ls_school_id', table_name='live_sessions')
    op.drop_index('ix_ls_class_id', table_name='live_sessions')
    op.drop_index('ix_ls_teacher_id', table_name='live_sessions')
    op.drop_table('live_sessions')

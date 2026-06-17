"""schedules and lessons

Revision ID: 003
Revises: 002
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.SmallInteger(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('duration_min', sa.SmallInteger(), nullable=False, server_default='60'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_min', sa.SmallInteger(), nullable=False, server_default='60'),
        sa.Column('zoom_link', sa.String(512), nullable=True),
        sa.Column('status', sa.String(16), nullable=False, server_default='scheduled'),
        sa.Column('reminder_24h_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reminder_2h_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reminder_30m_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_lessons_scheduled_at', 'lessons', ['scheduled_at'])
    op.create_index('idx_lessons_group_id', 'lessons', ['group_id'])


def downgrade() -> None:
    op.drop_index('idx_lessons_group_id', table_name='lessons')
    op.drop_index('idx_lessons_scheduled_at', table_name='lessons')
    op.drop_table('lessons')
    op.drop_table('schedules')

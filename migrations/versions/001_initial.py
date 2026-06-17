"""initial

Revision ID: 001
Revises:
Create Date: 2026-06-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(64), nullable=True),
        sa.Column('language', sa.String(2), nullable=False, server_default='uk'),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
    )

    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(128), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('parent_name', sa.String(128), nullable=True),
        sa.Column('parent_phone', sa.String(20), nullable=True),
        sa.Column('study_start_month', sa.String(7), nullable=True),
        sa.Column('study_format', sa.String(16), nullable=True),
        sa.Column('extra_info', sa.Text(), nullable=True),
        sa.Column('notion_link', sa.String(512), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'teacher_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(128), nullable=False),
        sa.Column('photo_file_id', sa.String(256), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('specialization', sa.String(256), nullable=True),
        sa.Column('experience_years', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'invite_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(16), nullable=False, server_default='teacher'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_by', sa.Integer(), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['used_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )

    op.create_table(
        'agreements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(16), nullable=False),
        sa.Column('agreed_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'admin_actions_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(128), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id']),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('admin_actions_log')
    op.drop_table('agreements')
    op.drop_table('invite_codes')
    op.drop_table('teacher_profiles')
    op.drop_table('student_profiles')
    op.drop_table('users')

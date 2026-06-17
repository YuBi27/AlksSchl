"""teacher module

Revision ID: 004
Revises: 003
Create Date: 2026-06-17 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'attendances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('student_user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lesson_id', 'student_user_id', name='uq_attendances_lesson_student'),
    )
    op.create_index('idx_attendances_lesson_id', 'attendances', ['lesson_id'])
    op.create_index('idx_attendances_student_user_id', 'attendances', ['student_user_id'])

    op.create_table(
        'homeworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('student_user_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_homeworks_teacher_id', 'homeworks', ['teacher_id'])
    op.create_index('idx_homeworks_group_id', 'homeworks', ['group_id'])
    op.create_index('idx_homeworks_student_user_id', 'homeworks', ['student_user_id'])

    op.create_table(
        'homework_grades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('homework_id', sa.Integer(), nullable=False),
        sa.Column('student_user_id', sa.Integer(), nullable=False),
        sa.Column('graded_by', sa.Integer(), nullable=True),
        sa.Column('grade_text', sa.String(512), nullable=False),
        sa.Column('graded_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['homework_id'], ['homeworks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['graded_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('homework_id', 'student_user_id', name='uq_homework_grades_hw_student'),
    )

    op.create_table(
        'teacher_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('student_user_id', sa.Integer(), nullable=True),
        sa.Column('lesson_id', sa.Integer(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_teacher_notes_student_user_id', 'teacher_notes', ['student_user_id'])
    op.create_index('idx_teacher_notes_lesson_id', 'teacher_notes', ['lesson_id'])


def downgrade() -> None:
    op.drop_index('idx_teacher_notes_lesson_id', table_name='teacher_notes')
    op.drop_index('idx_teacher_notes_student_user_id', table_name='teacher_notes')
    op.drop_table('teacher_notes')
    op.drop_table('homework_grades')
    op.drop_index('idx_homeworks_student_user_id', table_name='homeworks')
    op.drop_index('idx_homeworks_group_id', table_name='homeworks')
    op.drop_index('idx_homeworks_teacher_id', table_name='homeworks')
    op.drop_table('homeworks')
    op.drop_index('idx_attendances_student_user_id', table_name='attendances')
    op.drop_index('idx_attendances_lesson_id', table_name='attendances')
    op.drop_table('attendances')

"""SP7 quizzes tables

Revision ID: 010
Revises: 009
Create Date: 2026-06-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quizzes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('time_limit_min', sa.Integer()),
        sa.Column('shuffle_questions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_table(
        'quiz_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_idx', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(16), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('file_id', sa.String(256)),
    )
    op.create_table(
        'quiz_options',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text', sa.String(512), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_table(
        'quiz_assignments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id', ondelete='CASCADE')),
        sa.Column('student_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('deadline', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint(
            "(group_id IS NULL) != (student_user_id IS NULL)",
            name="quiz_assignment_exactly_one_target",
        ),
    )
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('quiz_id', sa.Integer(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assignment_id', sa.Integer(), sa.ForeignKey('quiz_assignments.id', ondelete='SET NULL')),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('finished_at', sa.DateTime(timezone=True)),
        sa.Column('score', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.Column('max_score', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(16), nullable=False, server_default='in_progress'),
    )
    op.create_table(
        'quiz_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('attempt_id', sa.Integer(), sa.ForeignKey('quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('selected_options', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('text_answer', sa.Text()),
        sa.Column('is_correct', sa.Boolean()),
        sa.Column('points_earned', sa.Numeric(6, 2), nullable=False, server_default='0'),
        sa.UniqueConstraint('attempt_id', 'question_id', name='uq_quiz_answer'),
    )


def downgrade() -> None:
    op.drop_table('quiz_answers')
    op.drop_table('quiz_attempts')
    op.drop_table('quiz_assignments')
    op.drop_table('quiz_options')
    op.drop_table('quiz_questions')
    op.drop_table('quizzes')

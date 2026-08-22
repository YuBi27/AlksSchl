"""individual lessons - make group_id nullable, add student_user_id

Revision ID: 005
Revises: 004
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('lessons', 'group_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('lessons', sa.Column('student_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_lessons_student_user_id', 'lessons', 'users',
        ['student_user_id'], ['id'], ondelete='CASCADE'
    )
    op.create_index('idx_lessons_student_user_id', 'lessons', ['student_user_id'])


def downgrade() -> None:
    op.drop_index('idx_lessons_student_user_id', table_name='lessons')
    op.drop_constraint('fk_lessons_student_user_id', 'lessons', type_='foreignkey')
    op.drop_column('lessons', 'student_user_id')
    op.alter_column('lessons', 'group_id', existing_type=sa.Integer(), nullable=False)

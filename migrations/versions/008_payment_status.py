"""Add status column to payments

Revision ID: 008
Revises: 007
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payments',
        sa.Column('status', sa.String(24), nullable=False, server_default='created'),
    )
    op.create_index('ix_payments_status', 'payments', ['status'])


def downgrade() -> None:
    op.drop_index('ix_payments_status', 'payments')
    op.drop_column('payments', 'status')

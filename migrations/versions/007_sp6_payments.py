"""SP6 payments table

Revision ID: 007
Revises: 006
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('payment_type', sa.String(16), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_payments_user_id', 'payments', ['user_id'])
    op.create_index('idx_payments_period_end', 'payments', ['period_end'])

    op.execute("""
        INSERT INTO bot_content (key, value)
        VALUES ('payment_details', 'Реквізити для оплати ще не додані. Зверніться до адміністратора.')
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_index('idx_payments_period_end', table_name='payments')
    op.drop_index('idx_payments_user_id', table_name='payments')
    op.drop_table('payments')

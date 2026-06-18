"""SP5 broadcasts and bot_content tables

Revision ID: 006
Revises: 005
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'broadcasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=True),
        sa.Column('target_type', sa.String(32), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('message_type', sa.String(16), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('file_id', sa.String(256), nullable=True),
        sa.Column('recipient_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_broadcasts_sender_id', 'broadcasts', ['sender_id'])
    op.create_index('idx_broadcasts_sent_at', 'broadcasts', ['sent_at'])

    op.create_table(
        'bot_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(64), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='uq_bot_content_key'),
    )

    # Seed default content rows
    op.execute("""
        INSERT INTO bot_content (key, value) VALUES
        ('school_rules', 'Правила школи ще не додані.'),
        ('price_list', 'Цінова політика ще не додана.'),
        ('school_info', 'Контактна інформація ще не додана.')
    """)


def downgrade() -> None:
    op.drop_index('idx_broadcasts_sent_at', table_name='broadcasts')
    op.drop_index('idx_broadcasts_sender_id', table_name='broadcasts')
    op.drop_table('broadcasts')
    op.drop_table('bot_content')

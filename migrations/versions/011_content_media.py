"""add file_id and file_type to bot_content

Revision ID: 011
Revises: 010
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_content", sa.Column("file_id", sa.String(256), nullable=True))
    op.add_column("bot_content", sa.Column("file_type", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("bot_content", "file_type")
    op.drop_column("bot_content", "file_id")

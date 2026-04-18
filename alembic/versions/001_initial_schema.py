"""Initial schema: chats, message tracks, api cache, kv store.

Revision ID: 001_initial
Revises:
Create Date: 2026-04-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_chats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_chat_id"),
    )
    op.create_index("ix_telegram_chats_telegram_chat_id", "telegram_chats", ["telegram_chat_id"], unique=False)

    op.create_table(
        "bot_message_tracks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("telegram_message_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["telegram_chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chat_id", "telegram_message_id", name="uq_track_chat_message"),
    )
    op.create_index("ix_bot_message_tracks_scope", "bot_message_tracks", ["scope"], unique=False)

    op.create_table(
        "api_cache_entries",
        sa.Column("cache_key", sa.String(length=512), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("cache_key"),
    )
    op.create_index("ix_api_cache_expires_at", "api_cache_entries", ["expires_at"], unique=False)

    op.create_table(
        "app_kv_store",
        sa.Column("key", sa.String(length=256), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("app_kv_store")
    op.drop_index("ix_api_cache_expires_at", table_name="api_cache_entries")
    op.drop_table("api_cache_entries")
    op.drop_index("ix_bot_message_tracks_scope", table_name="bot_message_tracks")
    op.drop_table("bot_message_tracks")
    op.drop_index("ix_telegram_chats_telegram_chat_id", table_name="telegram_chats")
    op.drop_table("telegram_chats")

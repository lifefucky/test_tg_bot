from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatUpsert(BaseModel):
    """Input for upserting a Telegram chat row."""

    telegram_chat_id: int = Field(..., description="Telegram chat id (same as user id in private chats)")
    chat_type: str
    title: str | None = None


class ChatRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_chat_id: int
    chat_type: str
    title: str | None
    created_at: datetime
    updated_at: datetime

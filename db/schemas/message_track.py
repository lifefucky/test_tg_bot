from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageTrackCreate(BaseModel):
    telegram_message_id: int
    scope: str
    sort_order: int = 0


class MessageTrackRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: int
    telegram_message_id: int
    scope: str
    sort_order: int
    created_at: datetime


class MessageIdsResult(BaseModel):
    """Telegram message ids removed or listed for a scope."""

    telegram_message_ids: list[int] = Field(default_factory=list)

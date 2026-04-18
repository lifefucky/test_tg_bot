from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class BotMessageTrack(Base):
    __tablename__ = "bot_message_tracks"
    __table_args__ = (UniqueConstraint("chat_id", "telegram_message_id", name="uq_track_chat_message"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("telegram_chats.id", ondelete="CASCADE"), nullable=False)
    telegram_message_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chat: Mapped["TelegramChat"] = relationship("TelegramChat", back_populates="message_tracks")

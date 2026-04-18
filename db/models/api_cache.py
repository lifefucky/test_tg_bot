from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class ApiCacheEntry(Base):
    __tablename__ = "api_cache_entries"
    __table_args__ = (Index("ix_api_cache_expires_at", "expires_at"),)

    cache_key: Mapped[str] = mapped_column(String(512), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

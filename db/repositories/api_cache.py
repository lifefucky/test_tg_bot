from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ApiCacheEntry


async def get_json(session: AsyncSession, cache_key: str) -> Any | None:
    row = await session.scalar(select(ApiCacheEntry).where(ApiCacheEntry.cache_key == cache_key))
    if row is None:
        return None
    if row.expires_at is not None and row.expires_at <= datetime.now(timezone.utc):
        await session.delete(row)
        await session.flush()
        return None
    return json.loads(row.payload_json)


async def set_json(
    session: AsyncSession,
    cache_key: str,
    value: Any,
    expires_at: datetime | None = None,
) -> None:
    payload = json.dumps(value, ensure_ascii=False)
    row = await session.scalar(select(ApiCacheEntry).where(ApiCacheEntry.cache_key == cache_key))
    if row is None:
        session.add(
            ApiCacheEntry(cache_key=cache_key, payload_json=payload, expires_at=expires_at)
        )
    else:
        row.payload_json = payload
        row.expires_at = expires_at
    await session.flush()


async def clear_all(session: AsyncSession) -> None:
    await session.execute(delete(ApiCacheEntry))
    await session.flush()

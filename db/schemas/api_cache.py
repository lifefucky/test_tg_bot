from datetime import datetime

from pydantic import BaseModel, Field


class ApiCacheSet(BaseModel):
    cache_key: str
    payload_json: str
    expires_at: datetime | None = None


class ApiCacheRead(BaseModel):
    cache_key: str
    payload_json: str
    expires_at: datetime | None = None

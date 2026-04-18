"""Database URL from environment (see example.env)."""

from os import environ
from typing import Final

# In-memory async SQLite by default; use StaticPool in session factory for a single shared DB.
DEFAULT_DATABASE_URL: Final = "sqlite+aiosqlite:///:memory:"


def get_database_url() -> str:
    url = environ.get("DATABASE_URL", DEFAULT_DATABASE_URL).strip()
    return url or DEFAULT_DATABASE_URL


def is_in_memory_sqlite(url: str) -> bool:
    u = url.lower()
    return ":memory:" in u or "mode=memory" in u

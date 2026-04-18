"""Repository tests (async SQLite in memory)."""

import os

import pytest

from db.repositories import api_cache, chats, message_tracks
from db.schemas.chat import ChatUpsert
from db.session import bind_engine, create_async_engine_from_url, get_session_maker, init_db_schema, reset_engine


@pytest.fixture(autouse=True)
def _isolate_database_url():
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield
    if prev is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = prev
    reset_engine()


@pytest.fixture
async def session():
    reset_engine()
    engine = create_async_engine_from_url(os.environ["DATABASE_URL"])
    bind_engine(engine)
    await init_db_schema(engine)
    maker = get_session_maker()
    async with maker() as s:
        yield s
        await s.commit()


@pytest.mark.asyncio
async def test_upsert_chat_inserts_then_updates(session):
    row = await chats.upsert_chat(
        session,
        ChatUpsert(telegram_chat_id=42, chat_type="private", title=None),
    )
    assert row.telegram_chat_id == 42
    assert row.chat_type == "private"

    row2 = await chats.upsert_chat(
        session,
        ChatUpsert(telegram_chat_id=42, chat_type="private", title="x"),
    )
    assert row2.id == row.id
    assert row2.title == "x"


@pytest.mark.asyncio
async def test_message_tracks_list_delete(session):
    chat = await chats.upsert_chat(
        session,
        ChatUpsert(telegram_chat_id=100, chat_type="private", title=None),
    )
    internal_id = chat.id
    await message_tracks.add_track(
        session,
        chat_internal_id=internal_id,
        telegram_message_id=1,
        scope="procedures",
        sort_order=0,
    )
    await message_tracks.add_track(
        session,
        chat_internal_id=internal_id,
        telegram_message_id=2,
        scope="procedures",
        sort_order=1,
    )
    await session.flush()

    ids = await message_tracks.list_message_ids_for_scope(
        session, telegram_chat_id=100, scope="procedures"
    )
    assert ids == [1, 2]

    removed = await message_tracks.delete_tracks_for_scope(
        session, telegram_chat_id=100, scope="procedures"
    )
    assert set(removed) == {1, 2}

    again = await message_tracks.list_message_ids_for_scope(
        session, telegram_chat_id=100, scope="procedures"
    )
    assert again == []


@pytest.mark.asyncio
async def test_api_cache_roundtrip_and_clear(session):
    await api_cache.set_json(session, "k1", [{"a": 1}])
    await session.flush()
    got = await api_cache.get_json(session, "k1")
    assert got == [{"a": 1}]

    await api_cache.clear_all(session)
    await session.flush()
    assert await api_cache.get_json(session, "k1") is None

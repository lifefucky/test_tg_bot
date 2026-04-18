from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BotMessageTrack, TelegramChat


async def add_track(
    session: AsyncSession,
    *,
    chat_internal_id: int,
    telegram_message_id: int,
    scope: str,
    sort_order: int = 0,
) -> None:
    session.add(
        BotMessageTrack(
            chat_id=chat_internal_id,
            telegram_message_id=telegram_message_id,
            scope=scope,
            sort_order=sort_order,
        )
    )


async def list_message_ids_for_scope(
    session: AsyncSession,
    *,
    telegram_chat_id: int,
    scope: str,
) -> list[int]:
    stmt = (
        select(BotMessageTrack.telegram_message_id)
        .join(TelegramChat, TelegramChat.id == BotMessageTrack.chat_id)
        .where(
            TelegramChat.telegram_chat_id == telegram_chat_id,
            BotMessageTrack.scope == scope,
        )
        .order_by(BotMessageTrack.sort_order, BotMessageTrack.id)
    )
    rows = await session.scalars(stmt)
    return list(rows.all())


async def delete_tracks_for_scope(
    session: AsyncSession,
    *,
    telegram_chat_id: int,
    scope: str,
) -> list[int]:
    ids = await list_message_ids_for_scope(session, telegram_chat_id=telegram_chat_id, scope=scope)
    chat_id_sq = select(TelegramChat.id).where(TelegramChat.telegram_chat_id == telegram_chat_id)
    await session.execute(
        delete(BotMessageTrack).where(
            BotMessageTrack.chat_id.in_(chat_id_sq),
            BotMessageTrack.scope == scope,
        )
    )
    return ids


async def delete_tracks_for_scopes(
    session: AsyncSession,
    *,
    telegram_chat_id: int,
    scopes: list[str],
) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for scope in scopes:
        out[scope] = await delete_tracks_for_scope(
            session, telegram_chat_id=telegram_chat_id, scope=scope
        )
    return out

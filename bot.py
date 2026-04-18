import asyncio
import logging
from typing import Any

from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from db import init_db_schema
from db.enums import MessageTrackScope
from db.repositories import api_cache, chats, message_tracks
from db.schemas.chat import ChatRow, ChatUpsert
from db.session import get_session_maker
from fetch_modules.online_trade import OnlineContract
from misc import TgKeys
from utils import (
    beautiful_positions,
    beautiful_procedure,
    onlc_text_and_data,
    split_telegram_messages,
)
from utils.callbacks import parse_pagination_callback

PAGE_SIZE = 7
SEND_DELAY = 0.06

bot = Bot(token=TgKeys.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

CATEGORY_CALLBACK_IDS = frozenset(data for _, data in onlc_text_and_data)


def _chat_type_str(chat: Any) -> str:
    t = getattr(chat, "type", None)
    if t is None:
        return "private"
    return str(t.value) if hasattr(t, "value") else str(t)


def _chat_upsert_from_message(message: Message) -> ChatUpsert:
    ch = message.chat
    title = getattr(ch, "title", None)
    return ChatUpsert(
        telegram_chat_id=ch.id,
        chat_type=_chat_type_str(ch),
        title=title,
    )


def _chat_upsert_from_callback(query: CallbackQuery) -> ChatUpsert:
    if query.message and query.message.chat:
        ch = query.message.chat
        return ChatUpsert(
            telegram_chat_id=ch.id,
            chat_type=_chat_type_str(ch),
            title=getattr(ch, "title", None),
        )
    uid = query.from_user.id if query.from_user else 0
    return ChatUpsert(telegram_chat_id=uid, chat_type="private", title=None)


def _telegram_chat_id_from_callback(query: CallbackQuery) -> int:
    if query.message and query.message.chat:
        return query.message.chat.id
    return query.from_user.id


async def _delete_telegram_messages(telegram_chat_id: int, message_ids: list[int]) -> None:
    for mid in message_ids:
        try:
            await bot.delete_message(telegram_chat_id, mid)
        except Exception:
            pass
        await asyncio.sleep(0.03)


class DbSessionMiddleware(BaseMiddleware):
    """One AsyncSession per update with commit on success."""

    async def __call__(
        self,
        handler: Any,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        maker = get_session_maker()
        async with maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


dp.update.middleware(DbSessionMiddleware())


async def _ensure_procedures(session: AsyncSession, cat_str: str):
    cached = await api_cache.get_json(session, cat_str)
    if cached is not None:
        return cached
    id_list = cat_str.split(",")
    oc = OnlineContract()
    data = await asyncio.to_thread(oc.get_procedures, id_list)
    if data is None:
        return None
    await api_cache.set_json(session, cat_str, data)
    return data


async def _render_procedure_chunk(
    session: AsyncSession,
    chat_row: ChatRow,
    telegram_chat_id: int,
    cat_str: str,
    offset: int,
) -> None:
    rows = await _ensure_procedures(session, cat_str)
    internal_id = chat_row.id

    async def _track_sent(message_id: int, sort_order: int) -> None:
        await message_tracks.add_track(
            session,
            chat_internal_id=internal_id,
            telegram_message_id=message_id,
            scope=MessageTrackScope.procedures,
            sort_order=sort_order,
        )

    if rows is None:
        m = await bot.send_message(
            telegram_chat_id,
            "Не удалось загрузить список процедур. Попробуйте позже.",
        )
        await _track_sent(m.message_id, offset * PAGE_SIZE + 999)
        return
    if not rows:
        m = await bot.send_message(
            telegram_chat_id,
            "На текущий момент в данной категории нет актуальных процедур.",
        )
        await _track_sent(m.message_id, offset * PAGE_SIZE + 998)
        return

    page = rows[offset : offset + PAGE_SIZE]
    for idx, item in enumerate(page):
        if idx > 0:
            await asyncio.sleep(SEND_DELAY)
        card = beautiful_procedure(item)
        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Позиции", callback_data=f"pos_{item['id']}")]
            ]
        )
        msg = await bot.send_message(
            chat_id=telegram_chat_id, text=card, reply_markup=keyboard_markup
        )
        await _track_sent(msg.message_id, offset * PAGE_SIZE + idx)

    next_off = offset + PAGE_SIZE
    if next_off < len(rows):
        more_cb = f"m|{next_off}|{cat_str}"
        if len(more_cb.encode("utf-8")) > 64:
            logging.warning("callback_data exceeds 64 bytes: %r", more_cb)
        else:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Показать ещё", callback_data=more_cb)]]
            )
            shown = offset + len(page)
            msg = await bot.send_message(
                telegram_chat_id,
                f"Показано {shown} из {len(rows)}.",
                reply_markup=kb,
            )
            await _track_sent(msg.message_id, offset * PAGE_SIZE + PAGE_SIZE)


@dp.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession) -> None:
    await api_cache.clear_all(session)

    chat_row = await chats.upsert_chat(session, _chat_upsert_from_message(message))
    tid = message.chat.id
    for scope in (
        MessageTrackScope.procedures,
        MessageTrackScope.positions,
        MessageTrackScope.welcome,
    ):
        ids = await message_tracks.delete_tracks_for_scope(session, telegram_chat_id=tid, scope=scope)
        await _delete_telegram_messages(tid, ids)

    text = (
        "Бот показывает открытые процедуры с площадки onlinecontract.ru "
        "по бытовой химии, хозтоварам и смежным темам.\n\n"
        "Выберите категорию — пришлём карточки торгов; по кнопке «Позиции» "
        "откроется конкурсный лист.\n\n"
        "<b>Чаще всего выбирают:</b> «Бытовая химия» или сразу «Все выбранные категории»."
    )
    sent = await message.reply(text, reply_markup=_category_keyboard())
    await message_tracks.add_track(
        session,
        chat_internal_id=chat_row.id,
        telegram_message_id=sent.message_id,
        scope=MessageTrackScope.welcome,
        sort_order=0,
    )
    try:
        await bot.pin_chat_message(tid, sent.message_id, disable_notification=True)
    except Exception:
        logging.debug("pin_chat_message skipped", exc_info=True)


def _category_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=text, callback_data=data)] for text, data in onlc_text_and_data
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.reply(
        "Как пользоваться:\n"
        "• /start — выбрать тематику и получить список процедур.\n"
        "• По кнопке «Позиции» под карточкой — конкурсный лист по этой процедуре.\n"
        "• Если торгов много, они приходят частями — внизу будет кнопка «Показать ещё».\n\n"
        "Команда /clear пытается удалить до 30 последних сообщений в чате (только то, что бот может удалить)."
    )


@dp.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    chat_id = message.chat.id
    start = message.message_id - 1
    for i in range(30):
        mid = start - i
        if mid < 0:
            break
        try:
            await bot.delete_message(chat_id, mid)
        except Exception:
            pass
        await asyncio.sleep(0.05)
    try:
        await message.delete()
    except Exception:
        pass


@dp.callback_query(F.data.startswith("m|"))
async def on_procedures_more(query: CallbackQuery, session: AsyncSession) -> None:
    await query.answer()
    try:
        offset, cat_str = parse_pagination_callback(query.data)
    except (ValueError, IndexError):
        await bot.send_message(query.from_user.id, "Некорректная кнопка. Нажмите /start.")
        return
    chat_row = await chats.upsert_chat(session, _chat_upsert_from_callback(query))
    tid = _telegram_chat_id_from_callback(query)
    await _render_procedure_chunk(session, chat_row, tid, cat_str, offset)


@dp.callback_query(F.data.in_(CATEGORY_CALLBACK_IDS))
async def on_category_selected(query: CallbackQuery, session: AsyncSession) -> None:
    await query.answer("Загружаем список…")
    cat_str = query.data or ""
    chat_row = await chats.upsert_chat(session, _chat_upsert_from_callback(query))
    tid = _telegram_chat_id_from_callback(query)

    proc_ids = await message_tracks.delete_tracks_for_scope(
        session, telegram_chat_id=tid, scope=MessageTrackScope.procedures
    )
    await _delete_telegram_messages(tid, proc_ids)

    status = await bot.send_message(tid, "Ищу процедуры…")
    await _ensure_procedures(session, cat_str)
    try:
        await bot.delete_message(tid, status.message_id)
    except Exception:
        pass
    await _render_procedure_chunk(session, chat_row, tid, cat_str, 0)


@dp.callback_query(F.data.startswith("pos_"))
async def on_positions(callback_query: CallbackQuery, session: AsyncSession) -> None:
    await callback_query.answer("Готовлю конкурсный лист…")
    procedure_id = callback_query.data.split("_", 1)[1]
    chat_row = await chats.upsert_chat(session, _chat_upsert_from_callback(callback_query))
    tid = _telegram_chat_id_from_callback(callback_query)

    pos_ids = await message_tracks.delete_tracks_for_scope(
        session, telegram_chat_id=tid, scope=MessageTrackScope.positions
    )
    await _delete_telegram_messages(tid, pos_ids)

    oc = OnlineContract()
    data = await asyncio.to_thread(oc.get_positions, procedure_id)

    internal_id = chat_row.id

    async def _track_pos(message_id: int, order: int) -> None:
        await message_tracks.add_track(
            session,
            chat_internal_id=internal_id,
            telegram_message_id=message_id,
            scope=MessageTrackScope.positions,
            sort_order=order,
        )

    if data is None:
        m = await bot.send_message(
            tid,
            "Не удалось загрузить позиции. Попробуйте позже.",
        )
        await _track_pos(m.message_id, 0)
        return

    card = beautiful_positions(data)
    if not card.strip():
        m = await bot.send_message(tid, "Нет данных по позициям.")
        await _track_pos(m.message_id, 0)
        return

    for i, chunk in enumerate(split_telegram_messages(card)):
        if i > 0:
            await asyncio.sleep(SEND_DELAY)
        msg = await bot.send_message(tid, chunk)
        await _track_pos(msg.message_id, i)


async def main() -> None:
    await init_db_schema()
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())

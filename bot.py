import asyncio
import logging

from aiogram import Bot, Dispatcher, executor, types

from fetch_modules.online_trade import OnlineContract
from misc import TgKeys
from utils import (
    beautiful_positions,
    beautiful_procedure,
    onlc_text_and_data,
    split_telegram_messages,
)

PAGE_SIZE = 7
SEND_DELAY = 0.06

bot = Bot(token=TgKeys.TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

CATEGORY_CALLBACK_IDS = frozenset(data for _, data in onlc_text_and_data)
_procedure_lists_cache: dict[str, list] = {}


def _reset_procedure_cache() -> None:
    _procedure_lists_cache.clear()


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    _reset_procedure_cache()
    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
    row_buttons = [
        types.InlineKeyboardButton(text, callback_data=data) for text, data in onlc_text_and_data
    ]
    keyboard_markup.add(*row_buttons)

    text = (
        "Бот показывает открытые процедуры с площадки onlinecontract.ru "
        "по бытовой химии, хозтоварам и смежным темам.\n\n"
        "Выберите категорию — пришлём карточки торгов; по кнопке «Позиции» "
        "откроется конкурсный лист.\n\n"
        "<b>Чаще всего выбирают:</b> «Бытовая химия» или сразу «Все выбранные категории»."
    )
    await message.reply(text, reply_markup=keyboard_markup)


@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.reply(
        "Как пользоваться:\n"
        "• /start — выбрать тематику и получить список процедур.\n"
        "• По кнопке «Позиции» под карточкой — конкурсный лист по этой процедуре.\n"
        "• Если торгов много, они приходят частями — внизу будет кнопка «Показать ещё».\n\n"
        "Команда /clear пытается удалить до 30 последних сообщений в чате (только то, что бот может удалить)."
    )


@dp.message_handler(commands=["clear"])
async def cmd_clear(message: types.Message):
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


async def _ensure_procedures(cat_str: str):
    if cat_str in _procedure_lists_cache:
        return _procedure_lists_cache[cat_str]
    id_list = cat_str.split(",")
    oc = OnlineContract()
    data = await asyncio.to_thread(oc.get_procedures, id_list)
    if data is None:
        return None
    _procedure_lists_cache[cat_str] = data
    return data


async def _render_procedure_chunk(chat_id: int, cat_str: str, offset: int) -> None:
    rows = await _ensure_procedures(cat_str)
    if rows is None:
        await bot.send_message(
            chat_id,
            "Не удалось загрузить список процедур. Попробуйте позже.",
        )
        return
    if not rows:
        await bot.send_message(
            chat_id,
            "На текущий момент в данной категории нет актуальных процедур.",
        )
        return

    page = rows[offset : offset + PAGE_SIZE]
    for idx, item in enumerate(page):
        if idx > 0:
            await asyncio.sleep(SEND_DELAY)
        card = beautiful_procedure(item)
        keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
        keyboard_markup.add(
            types.InlineKeyboardButton("Позиции", callback_data=f"pos_{item['id']}")
        )
        await bot.send_message(chat_id=chat_id, text=card, reply_markup=keyboard_markup)

    next_off = offset + PAGE_SIZE
    if next_off < len(rows):
        more_cb = f"m|{next_off}|{cat_str}"
        if len(more_cb.encode("utf-8")) > 64:
            logging.warning("callback_data exceeds 64 bytes: %r", more_cb)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Показать ещё", callback_data=more_cb))
            shown = offset + len(page)
            await bot.send_message(
                chat_id,
                f"Показано {shown} из {len(rows)}.",
                reply_markup=kb,
            )


@dp.callback_query_handler(lambda c: c.data and c.data.startswith("m|"))
async def on_procedures_more(query: types.CallbackQuery):
    await query.answer()
    try:
        _, off_s, cat_str = query.data.split("|", 2)
        offset = int(off_s)
    except (ValueError, IndexError):
        await bot.send_message(query.from_user.id, "Некорректная кнопка. Нажмите /start.")
        return
    await _render_procedure_chunk(query.from_user.id, cat_str, offset)


@dp.callback_query_handler(lambda c: c.data in CATEGORY_CALLBACK_IDS)
async def on_category_selected(query: types.CallbackQuery):
    await query.answer("Загружаем список…")
    cat_str = query.data
    chat_id = query.from_user.id
    status = await bot.send_message(chat_id, "Ищу процедуры…")
    await _ensure_procedures(cat_str)
    try:
        await bot.delete_message(chat_id, status.message_id)
    except Exception:
        pass
    await _render_procedure_chunk(chat_id, cat_str, 0)


@dp.callback_query_handler(lambda c: c.data.startswith("pos_"))
async def on_positions(callback_query: types.CallbackQuery):
    await callback_query.answer("Готовлю конкурсный лист…")
    procedure_id = callback_query.data.split("_", 1)[1]
    oc = OnlineContract()
    data = await asyncio.to_thread(oc.get_positions, procedure_id)

    if data is None:
        await bot.send_message(
            callback_query.from_user.id,
            "Не удалось загрузить позиции. Попробуйте позже.",
        )
        return

    card = beautiful_positions(data)
    if not card.strip():
        await bot.send_message(callback_query.from_user.id, "Нет данных по позициям.")
        return

    for chunk in split_telegram_messages(card):
        await bot.send_message(callback_query.from_user.id, chunk)
        await asyncio.sleep(SEND_DELAY)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

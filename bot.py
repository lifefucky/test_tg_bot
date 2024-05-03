import logging

from aiogram import Bot, Dispatcher, executor, types
from fetch_modules.online_trade import OnlineContract

import asyncio

from misc import TgKeys
from utils import beautiful_procedure, beautiful_positions
from utils import onlc_text_and_data

bot = Bot(token=TgKeys.TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

ids = list(data for text, data in onlc_text_and_data)

@dp.message_handler(commands='start')
async def start(message: types.Message):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    row_buttons = (types.InlineKeyboardButton(text, callback_data=data) for text, data in onlc_text_and_data)
    keyboard_markup.row(*row_buttons)

    await message.reply("Выберите предмет торгов:", reply_markup=keyboard_markup)

@dp.message_handler(commands='clear')
async def delete_messages(message: types.Message):
    for i in range(message.message_id, 1, -1):
        await bot.delete_message(message.from_user.id, i)



@dp.callback_query_handler(text=ids[0])
@dp.callback_query_handler(text=ids[1])
@dp.callback_query_handler(text=ids[2])
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer()

    answer_data = query.data
    id_list = answer_data.split(',')

    online_contract = OnlineContract()
    data = online_contract.get_procedures(categories=id_list)

    if data:
        for index, item in enumerate(data):
            card = beautiful_procedure(item)

            keyboard_markup = types.InlineKeyboardMarkup(row_width=1)
            row_buttons = types.InlineKeyboardButton("Позиции", callback_data=f"pos_{item['id']}")
            keyboard_markup.row(*[row_buttons])

            if index % 10 == 0:
                asyncio.sleep(3)

            await bot.send_message(chat_id=query.from_user.id, text=card, reply_markup=keyboard_markup)
    else:
        sorry_msg = "На текущий момент в данной категории нет актуальных процедур."
        await bot.send_message(query.from_user.id, sorry_msg)

@dp.callback_query_handler(lambda c: c.data.startswith("pos_"))
async def positions(callback_query: types.CallbackQuery):
    action = callback_query.data.split("_")[1]
    await callback_query.answer(text=action)

    online_contract = OnlineContract()
    data = online_contract.get_positions(procedure_id=action)

    if data:
        card = beautiful_positions(data)
        await bot.send_message(chat_id=callback_query.from_user.id, text=card)
    else:
        sorry_msg = "Ошибка!"
        await bot.send_message(callback_query.from_user.id, sorry_msg)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


#пробросить поставщика в карточку позиций
#на случай, если слишком большое - либо разбиваем на несколько, либо кратко описываем позиции, а потом линк


# Архитектура приложения

Достоверное описание потоков и границ компонентов. Детали реализации — в исходниках и в профильных файлах [`docs/`](.).

## Назначение

Telegram-бот на **aiogram 3.x** запрашивает у публичного API **onlinecontract.ru** (`api.onlc.ru`) список открытых процедур по выбранным категориям и отдаёт пользователю карточки; по кнопке загружает позиции (конкурсный лист) по процедуре.

## Внешние источники и ограничения

| Источник | Для чего смотреть |
|----------|-------------------|
| [Telegram Bot API](https://core.telegram.org/bots/api) | Лимиты сообщений (4096 символов), callback_data (до 64 байт), flood control |
| [aiogram 3.x](https://docs.aiogram.dev/en/latest/) | Обработчики, `Bot`, `Dispatcher`, middleware, HTML parse mode |
| Код [`fetch_modules/online_trade.py`](../fetch_modules/online_trade.py) | Фактические URL и query к `api.onlc.ru` (публичная спецификация площадки в репозитории не хранится) |

## Структура репозитория (логические слои)

```text
bot.py              — точка входа, middleware с сессией БД, маршрутизация update → handlers
db/                 — персистентный слой (подробно — database.md)
alembic/            — миграции схемы
fetch_modules/      — синхронный HTTP-клиент к API (вызов из asyncio через to_thread)
misc/               — TOKEN (TgKeys), DATABASE_URL (db_url.py)
utils/              — форматирование текста для Telegram, конфиг категорий для клавиатуры
```

Персистентность (SQLite, SQLAlchemy async, Pydantic, Alembic, кэш и трекинг сообщений) описана в **[`database.md`](database.md)** — здесь не дублируется.

## Поток данных

```mermaid
flowchart LR
  user[User] --> tg[Telegram]
  tg --> bot[bot.py]
  bot --> db[(SQLite)]
  bot --> oc[OnlineContract]
  oc --> api["api.onlc.ru"]
  bot --> fmt[beautiful_msg]
  fmt --> tg
```

1. Пользователь выбирает категорию → `callback_data` из [`utils/categories.py`](../utils/categories.py) → `_ensure_procedures` (кэш в БД или запрос) → `OnlineContract.get_procedures` (в `to_thread`).
2. Карточки процедур рендерятся через `beautiful_procedure`; пагинация — callback вида `m|<offset>|<cat_str>` (см. [`bot.py`](../bot.py)).
3. «Позиции» → `pos_<id>` → `get_positions` → `beautiful_positions`; длинный текст режется через `split_telegram_messages`.

## Согласованность данных

- Кнопки категорий: кортеж **`onlc_text_and_data`** и множество **`CATEGORY_CALLBACK_IDS`** в [`bot.py`](../bot.py) должны совпадать по вторым элементам (строка id для API).

## Пакеты (углублённо)

- HTTP и модель ответов API: [`fetch_modules.md`](fetch_modules.md)
- Токен и окружение: [`misc.md`](misc.md), [`example.env`](../example.env)
- База данных, миграции, ORM: [`database.md`](database.md)
- Тексты и HTML: [`utils.md`](utils.md)

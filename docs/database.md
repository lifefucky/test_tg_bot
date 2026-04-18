# База данных: SQLAlchemy, Pydantic, Alembic

Единая точка описания персистентного слоя. Код — в [`db/`](../db/), миграции — в [`alembic/`](../alembic/).

## Стек

| Компонент | Роль |
|-----------|------|
| **SQLAlchemy 2.x** (async) | ORM, `AsyncSession`, модели на [`DeclarativeBase`](../db/base.py) |
| **aiosqlite** | Асинхронный драйвер SQLite |
| **Pydantic v2** | Схемы входа/выхода репозиториев в [`db/schemas/`](../db/schemas/), без протаскивания ORM в Telegram API |
| **Alembic** | Версионирование схемы; async-окружение — [`alembic/env.py`](../alembic/env.py) |

Зависимости перечислены в [`requirements.txt`](../requirements.txt).

## Конфигурация URL

Переменная окружения **`DATABASE_URL`** задаётся в процессе (как и **`TOKEN`**); шаблон — [`example.env`](../example.env). Значение по умолчанию и вспомогательные проверки — [`misc/db_url.py`](../misc/db_url.py).

| Режим | Типичный URL | Примечание |
|-------|----------------|------------|
| In-memory | `sqlite+aiosqlite:///:memory:` | Один общий пул (**StaticPool** + `check_same_thread=False`), иначе у каждого соединения была бы своя пустая БД |
| Файл | `sqlite+aiosqlite:///./data/app.db` | Каталог `data/` создаётся при старте при необходимости; данные переживают перезапуск процесса |

## Инициализация схемы

[`db/session.py`](../db/session.py), функция **`init_db_schema()`**:

- для **in-memory** — `Base.metadata.create_all` на движке приложения;
- для **файлового** (и прочих не in-memory URL) — **`alembic upgrade head`** в отдельном потоке (`asyncio.to_thread`), чтобы не блокировать event loop.

Глобальные **`get_engine()`** / **`get_session_maker()`** кэшируют движок и фабрику сессий; для тестов есть **`bind_engine()`** и **`reset_engine()`**.

## Схема таблиц

| Таблица | Назначение |
|---------|------------|
| **`telegram_chats`** | Чат Telegram: внутренний `id`, `telegram_chat_id` (unique), `chat_type`, `title`, метки времени |
| **`bot_message_tracks`** | Учёт `telegram_message_id` по чату и **scope** (`procedures`, `positions`, `welcome`) для удаления старых сообщений при смене категории, новых «Позициях» и при `/start`; уникальность `(chat_id, telegram_message_id)` |
| **`api_cache_entries`** | Кэш JSON ответов `get_procedures` по ключу категории (`cache_key`); опционально `expires_at` |
| **`app_kv_store`** | Ключ–значение JSON для настроек и флагов (задел) |

ORM-модели: [`db/models/`](../db/models/). Перечисление scope: [`db/enums.py`](../db/enums.py) (`MessageTrackScope`).

## Репозитории и Pydantic

- Репозитории — тонкий слой над `AsyncSession`: [`db/repositories/chats.py`](../db/repositories/chats.py), [`message_tracks.py`](../db/repositories/message_tracks.py), [`api_cache.py`](../db/repositories/api_cache.py).
- Pydantic-модели — [`db/schemas/`](../db/schemas/) (например `ChatUpsert`, операции с кэшем).

## Миграции Alembic

- Конфиг: [`alembic.ini`](../alembic.ini); ревизии: [`alembic/versions/`](../alembic/versions/).
- URL в `env.py` подставляется из **`get_database_url()`**, путь к проекту добавляется в `sys.path`, чтобы импортировать пакет `db` без запуска бота.
- Ручной прогон из корня репозитория (после задания `DATABASE_URL` под файловый SQLite):

```bash
alembic upgrade head
```

Импорт **`misc.db_url`** не тянет **`TOKEN`** (см. ленивый `TgKeys` в [`misc/__init__.py`](../misc/__init__.py)), поэтому Alembic можно вызывать без переменной `TOKEN`.

## Связь с ботом

В [`bot.py`](../bot.py): middleware с одной **`AsyncSession`** на update и commit при успехе; кэш списков процедур и трекинг id сообщений идут через репозитории. Полная очистка кэша API на **`/start`** — см. `api_cache.clear_all`. Поведение UI (удаление сообщений, pin приветствия) согласовано с записями в `bot_message_tracks`.

## Тесты

Автотесты репозиториев: [`tests/test_db_repositories.py`](../tests/test_db_repositories.py) (изолированный in-memory движок в фикстуре). Общие правила pytest — [`testing.md`](testing.md).

## Сопровождение документации

При изменении схемы, способа миграций или контрактов репозиториев обновляйте этот файл; в [`architecture.md`](architecture.md) достаточно краткой отсылки на персистентный слой без повторения деталей.

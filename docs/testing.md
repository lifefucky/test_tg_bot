# Тестирование

## Автотесты (pytest)

Из корня репозитория:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Каталог: [`tests/`](../tests/). Перед импортом [`bot`](../bot.py) нужен **`TOKEN`** в окружении; для pytest в [`tests/conftest.py`](../tests/conftest.py) задаётся тестовый placeholder.

Покрытие:

| Файл | Содержание |
|------|------------|
| `test_beautiful_msg.py` | Форматирование карточек и `split_telegram_messages` |
| `test_online_trade.py` | `OnlineContract` с моком `requests.get` |
| `test_categories.py` | Согласованность `onlc_text_and_data` и `CATEGORY_CALLBACK_IDS` |
| `test_callbacks.py` | Парсинг callback пагинации |
| `test_db_repositories.py` | Репозитории БД (см. [`database.md`](database.md)) |

Настройки: [`pytest.ini`](../pytest.ini). Dev-зависимости: [`requirements-dev.txt`](../requirements-dev.txt).

На некоторых macOS с системным Python и LibreSSL urllib3 может выводить `NotOpenSSLWarning`; в `pytest.ini` оно отфильтровано, на работу тестов это не влияет. Обновить OpenSSL/Python или использовать venv с актуальным OpenSSL — по желанию.

## Ручная проверка (регрессия в Telegram)

1. **Запуск:** `TOKEN` в окружении (см. [`example.env`](../example.env)), затем `python bot.py` из корня проекта.
2. **Telegram:** `/start` — кнопки категорий; выбор категории — приходят карточки; при большом числе процедур — «Показать ещё»; «Позиции» — конкурсный лист (при очень длинном тексте — несколько сообщений).
3. **Сбои API:** при недоступности `api.onlc.ru` бот должен отвечать текстом об ошибке, а не падать (см. обработку `None` в [`bot.py`](../bot.py)).

## Связанные документы

- Зависимости и версия Python: [`requirements.txt`](../requirements.txt)
- Поведение бота: [`architecture.md`](architecture.md), [`bot.py`](../bot.py)
- БД и тесты репозиториев: [`database.md`](database.md)

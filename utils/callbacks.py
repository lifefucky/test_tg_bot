"""Pure helpers for Telegram callback_data (testable without Bot)."""


def parse_pagination_callback(data: str) -> tuple[int, str]:
    """
    Parse ``m|<offset>|<cat_str>`` from «Показать ещё».
    Raises ValueError / IndexError on bad input (same as naive split).
    """
    _, off_s, cat_str = data.split("|", 2)
    return int(off_s), cat_str

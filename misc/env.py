from os import environ
from typing import Final

_token = environ.get("TOKEN", "").strip()
if not _token:
    raise RuntimeError(
        "Environment variable TOKEN is not set. Export TOKEN before starting the bot."
    )


class TgKeys:
    TOKEN: Final = _token

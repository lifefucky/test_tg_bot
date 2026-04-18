"""Misc helpers (lazy TgKeys so importing e.g. ``misc.db_url`` does not require TOKEN)."""

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "TgKeys":
        from misc.env import TgKeys

        return TgKeys
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["TgKeys"]

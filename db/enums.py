from enum import StrEnum


class MessageTrackScope(StrEnum):
    """Tracked bot message groups for UI cleanup (extensible)."""

    procedures = "procedures"
    positions = "positions"
    welcome = "welcome"

from datetime import datetime, timezone

from structlog.typing import EventDict


def add_text_time(_1, _2, event_dict: EventDict) -> EventDict:
    event_dict["time"] = (
        datetime.now(tz=timezone.utc)
        .astimezone()
        .replace(tzinfo=None)
        .isoformat(sep=" ", timespec="milliseconds")
    )
    return event_dict

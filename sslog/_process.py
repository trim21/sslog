from datetime import datetime

from structlog.typing import EventDict, WrappedLogger


def add_time(_1: WrappedLogger, _2: str, event_dict: EventDict) -> EventDict:
    event_dict["time"] = datetime.now().astimezone().isoformat(timespec="microseconds")
    return event_dict

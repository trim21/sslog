import contextlib
import json
import logging
from datetime import datetime
from typing import Any, Protocol

import sys

from structlog.typing import EventDict
import structlog
from structlog.contextvars import bind_contextvars, reset_contextvars

from . import _default

if sys.version_info >= (3, 11,):
    from typing import Self
else:
    from typing_extensions import Self

__all__ = ["context", "logger"]


class _ConsoleRender(structlog.dev.ConsoleRenderer):

    def _repr(self, val: Any) -> str:
        return repr(val)


def __json_pre(_1, _2, event_dict: EventDict) -> EventDict:
    now = datetime.now()

    r = {
        "time": now.astimezone().isoformat(timespec="microseconds"),
        "timestamp": now.timestamp(),
    }

    msg = event_dict.pop("event", None)
    if msg is not None:
        r["msg"] = msg

    r["extra"] = event_dict
    return r


if _default.use_json:
    structlog.configure(
        processors=[
            __json_pre,
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.PATHNAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.THREAD,
                    structlog.processors.CallsiteParameter.PROCESS,
                ]
            ),
            structlog.dev.set_exc_info,
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(json.dumps, default=str),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

else:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(
                fmt="%Y-%m-%d %H:%M:%S.%f", utc=False, key="time"
            ),
            structlog.contextvars.merge_contextvars,
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.THREAD,
                    structlog.processors.CallsiteParameter.PROCESS,
                ]
            ),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.EventRenamer("msg"),
            _ConsoleRender(
                timestamp_key="time",
                event_key="msg",
                pad_event=0,
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class _Logger(Protocol):
    def bind(self, **kwargs) -> Self: ...
    def unbind(self, *keys: str) -> Self: ...
    def try_unbind(self, *keys: str) -> Self: ...
    def new(self, **new_values: Any) -> Self: ...

    def debug(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def info(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def warning(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def warn(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def error(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def exception(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...
    def fatal(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...

    def log(
        self, level: int, event: str | None = None, *args: Any, **kw: Any
    ) -> Any: ...

    def setLevel(self, level: int) -> None: ...

    @property
    def level(self) -> int: ...

    @property
    def name(self) -> str: ...

    def isEnabledFor(self, level: int) -> bool: ...


logger: _Logger = structlog.get_logger()


@contextlib.contextmanager
def context(**kwargs):
    ctx = bind_contextvars(**kwargs)
    yield
    reset_contextvars(**ctx)

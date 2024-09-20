from __future__ import annotations

import contextlib
import json
import logging
from datetime import datetime
from logging import NOTSET
from typing import Any, Protocol, TypeVar, cast, Callable

import structlog
from structlog.dev import Column
from structlog.typing import EventDict
from typing_extensions import ParamSpec, Self, overload

from . import _default, _out, _process
from ._base import make_filtering_bound_logger


__all__ = ["logger", "LazyValue", "InterceptHandler"]

from ._default import LEVEL_TRACE

T = TypeVar("T")
K = TypeVar("K", bound=Any)
P = ParamSpec("P")


class LazyValue:
    fn: Callable[[], Any]

    __slots__ = ("fn",)

    def __init__(self, fn: Callable[[], Any]) -> None:
        self.fn = fn

    def __format__(self, format_spec: str) -> str:
        return format(self.fn(), format_spec)


class _LogLevelColumnFormatter:
    level_styles: dict[str, str] | None
    reset_style: str
    width: int

    def __init__(
        self,
        level_styles: dict[str, str],
        reset_style: str,
        width: int | None = None,
    ) -> None:
        self.level_styles = level_styles
        self.width = width or 0
        if level_styles:
            self.reset_style = reset_style
        else:
            self.reset_style = ""

    def __call__(self, key: str, value: object) -> str:
        level = cast(str, value)
        style = "" if self.level_styles is None else self.level_styles.get(level, "")

        return f"{style}[{level:{self.width}s}]{self.reset_style}"


class _ConsoleRender(structlog.dev.ConsoleRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._columns[1] = Column(
            "level",
            _LogLevelColumnFormatter(
                self._columns[1].formatter.level_styles,
                reset_style=self._columns[1].formatter.reset_style,
                width=7,
            ),
        )

    def _repr(self, val: Any) -> str:
        return repr(val)

    @staticmethod
    def get_default_level_styles(colors: bool = True) -> Any:
        c = structlog.dev.ConsoleRenderer.get_default_level_styles(colors)
        c["trace"] = structlog.dev.CYAN
        return c


_NOT_SET = object()

_start_up = datetime.now()


def __json_pre(_1, _2, event_dict: EventDict) -> EventDict:
    now = datetime.now()

    r = {
        "time": now.astimezone().isoformat(timespec="microseconds"),
        "timestamp": now.timestamp(),
        "elapsed": (now - _start_up).total_seconds(),
    }

    msg = event_dict.pop("event", None)
    if msg is not None:
        r["msg"] = msg

    exc_info = event_dict.pop("exc_info", _NOT_SET)
    if exc_info is not _NOT_SET:
        r["exc_info"] = exc_info

    if event_dict:
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
                ],
                additional_ignores=["logging", "sslog"],
            ),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(json.dumps, default=str),
        ],
        wrapper_class=make_filtering_bound_logger(
            _default.LOGGING_LEVELS[_default.json_level.upper()]
        ),
        logger_factory=_out.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

else:
    structlog.configure(
        processors=[
            _process.add_text_time,
            structlog.contextvars.merge_contextvars,
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.MODULE,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.THREAD,
                ],
                additional_ignores=["logging", "sslog"],
            ),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.EventRenamer("msg"),
            _ConsoleRender(
                timestamp_key="time",
                event_key="msg",
                pad_event=40,
            ),
        ],
        wrapper_class=make_filtering_bound_logger(
            _default.LOGGING_LEVELS[_default.text_level.upper()]
        ),
        context_class=dict,
        logger_factory=lambda *args: _out.FlushLogger(),
        cache_logger_on_first_use=True,
    )


class _Logger(Protocol):
    def bind(self, **kwargs) -> Self: ...
    def unbind(self, *keys: str) -> Self: ...
    def try_unbind(self, *keys: str) -> Self: ...
    def new(self, **new_values: Any) -> Self: ...

    def trace(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def debug(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def info(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def warning(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def error(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def exception(self, event: str, *args: Any, **kw: Any) -> Any:
        """log a message at error level and capture current exception"""

    def fatal(self, event: str, *args: Any, **kw: Any) -> Any: ...

    def log(self, level: int, event: str, *args: Any, **kw: Any) -> Any: ...

    def setLevel(self, level: int) -> None: ...

    @property
    def level(self) -> int: ...

    @property
    def name(self) -> str: ...

    def isEnabledFor(self, level: int) -> bool: ...

    def contextualize(self, **kwargs) -> contextlib.AbstractContextManager[None]: ...

    @overload
    def catch(self, fn: T) -> T: ...

    @overload
    def catch(
        self,
        exc: type[BaseException] | tuple[type[BaseException], ...] = Exception,
        msg: str = ...,
    ) -> Catcher: ...

    def _proxy_to_logger(self, name: str, event: str | None, *args: Any) -> None: ...


class Catcher(Protocol):
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    def __call__(self, fn: T) -> T: ...


logger: _Logger = structlog.get_logger()


_STD_LEVEL_TO_NAME = {
    logging.FATAL: "FATAL".lower(),
    logging.ERROR: "ERROR".lower(),
    logging.WARNING: "WARNING".lower(),
    logging.INFO: "INFO".lower(),
    logging.DEBUG: "DEBUG".lower(),
    LEVEL_TRACE: "TRACE".lower(),
}


class InterceptHandler(logging.Handler):
    def __init__(self, level: int = NOTSET):
        super().__init__(max(level, logger.level))

    def handle(self, record):
        lvl = record.levelno
        if lvl < self.level:
            return

        lvl_name = _STD_LEVEL_TO_NAME[lvl]

        # Get corresponding level if it exists.
        return logger._proxy_to_logger(lvl_name, record.getMessage())

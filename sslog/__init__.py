from __future__ import annotations

import contextlib
import json
from datetime import datetime
from typing import Any, Protocol, TypeVar, cast

import structlog
from structlog.dev import Column
from structlog.typing import EventDict
from typing_extensions import ParamSpec, Self

from . import _default, _out, _process
from ._base import make_filtering_bound_logger


__all__ = ["logger"]


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
        self.width = width
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
                width=8,
            ),
        )

    def _repr(self, val: Any) -> str:
        return repr(val)


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
                # pad_event=0,
                pad_level=False,
            ),
        ],
        wrapper_class=make_filtering_bound_logger(
            _default.LOGGING_LEVELS[_default.text_level.upper()]
        ),
        context_class=dict,
        logger_factory=_out.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

T = TypeVar("T")
K = TypeVar("K", bound=Any)
P = ParamSpec("P")


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
    def critical(self, event: str | None = None, *args: Any, **kw: Any) -> Any: ...

    def log(
        self, level: int, event: str | None = None, *args: Any, **kw: Any
    ) -> Any: ...

    def setLevel(self, level: int) -> None: ...

    @property
    def level(self) -> int: ...

    @property
    def name(self) -> str: ...

    def isEnabledFor(self, level: int) -> bool: ...

    def contextualize(self, **kwargs) -> contextlib.AbstractContextManager[None]: ...

    def catch(
        self,
        exc: type[BaseException] | tuple[type[BaseException], ...] = Exception,
        msg: str = ...,
    ) -> Catcher: ...


class Catcher(Protocol):
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    def __call__(self, fn: T) -> T: ...


logger: _Logger = structlog.get_logger()

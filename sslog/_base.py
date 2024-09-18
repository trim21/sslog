from __future__ import annotations

import contextlib
import logging
from collections.abc import Callable
from inspect import isfunction
from typing import Any

from sslog._catch import Catcher
from structlog import BoundLoggerBase
from structlog.contextvars import bind_contextvars, reset_contextvars
from structlog.typing import FilteringBoundLogger

from sslog._default import LOGGING_LEVELS, LEVEL_TRACE


def _nop(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    return None


def exception(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    kw.setdefault("exc_info", True)

    return self.error(event, *args, **kw)


class FatalError(Exception):
    def __init__(self, msg: str, extra: dict[str, Any]):
        self.msg = msg
        self.extra = extra


def _fatal(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    if not args:
        msg = event
    else:
        msg = event.format(*args)

    self._proxy_to_logger("fatal", msg, **kw)

    raise FatalError(msg, kw)


def make_filtering_bound_logger(min_level: int) -> type[FilteringBoundLogger]:
    return LEVEL_TO_FILTERING_LOGGER[min_level]


class _BoundLoggerBase(BoundLoggerBase):
    @contextlib.contextmanager
    def contextualize(self, **kwargs):
        ctx = bind_contextvars(**kwargs)
        try:
            yield
        finally:
            reset_contextvars(**ctx)

    def catch(
        self,
        exc: type[BaseException] | tuple[type[BaseException], ...] = Exception,
        msg: str = "",
    ):
        if isfunction(exc):
            return Catcher(self, Exception, msg)(exc)
        return Catcher(self, exc, msg)(exc)


LEVEL_TO_NAME = {value: key.lower() for key, value in LOGGING_LEVELS.items()}


def _make_filtering_bound_logger(min_level: int) -> type:
    def make_method(level: int) -> Callable[..., Any]:
        if level < min_level:
            return _nop

        lvl_name = LEVEL_TO_NAME[level]

        def meth(self: Any, event: str, *args: Any, **kw: Any) -> Any:
            if not args:
                return self._proxy_to_logger(lvl_name, event, **kw)

            return self._proxy_to_logger(lvl_name, event.format(*args), **kw)

        meth.__name__ = lvl_name

        return meth

    meths: dict[str, Any] = {}
    for lvl, name in LEVEL_TO_NAME.items():
        meths[name] = make_method(lvl)

    meths["exception"] = exception
    meths["fatal"] = _fatal
    meths["msg"] = meths["info"]

    return type(
        f"BoundLoggerFilteringAt{LEVEL_TO_NAME[min_level].capitalize()}",
        (_BoundLoggerBase,),
        meths,
    )


# Pre-create all possible filters to make them pickleable.
BoundLoggerFilteringAtNotset = _make_filtering_bound_logger(logging.NOTSET)
BoundLoggerFilteringAtTrace = _make_filtering_bound_logger(LEVEL_TRACE)
BoundLoggerFilteringAtDebug = _make_filtering_bound_logger(logging.DEBUG)
BoundLoggerFilteringAtInfo = _make_filtering_bound_logger(logging.INFO)
BoundLoggerFilteringAtWarning = _make_filtering_bound_logger(logging.WARNING)
BoundLoggerFilteringAtError = _make_filtering_bound_logger(logging.ERROR)
BoundLoggerFilteringAtFatal = _make_filtering_bound_logger(logging.FATAL)

LEVEL_TO_FILTERING_LOGGER = {
    logging.FATAL: BoundLoggerFilteringAtFatal,
    logging.ERROR: BoundLoggerFilteringAtError,
    logging.WARNING: BoundLoggerFilteringAtWarning,
    logging.INFO: BoundLoggerFilteringAtInfo,
    logging.DEBUG: BoundLoggerFilteringAtDebug,
    LEVEL_TRACE: BoundLoggerFilteringAtTrace,
    logging.NOTSET: BoundLoggerFilteringAtNotset,
}

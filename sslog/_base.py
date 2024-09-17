from __future__ import annotations

import contextlib
import logging
import sys
from collections.abc import Callable
from inspect import isfunction
from typing import Any

from sslog._catch import Catcher
from structlog import BoundLoggerBase
from structlog._log_levels import LEVEL_TO_NAME
from structlog.contextvars import bind_contextvars, reset_contextvars
from structlog.typing import FilteringBoundLogger


def _nop(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    return None


def exception(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    kw.setdefault("exc_info", True)

    return self.error(event, *args, **kw)


def _fatal(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    if not args:
        self._proxy_to_logger("fatal", event, **kw)
    else:
        self._proxy_to_logger("fatal", event.format(*args), **kw)

    sys.exit(1)


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


def _make_filtering_bound_logger(min_level: int) -> type[FilteringBoundLogger]:
    def make_method(
        level: int,
    ) -> Callable[..., Any]:
        if level < min_level:
            return _nop

        name = LEVEL_TO_NAME[level]

        def meth(self: Any, event: str, *args: Any, **kw: Any) -> Any:
            if not args:
                return self._proxy_to_logger(name, event, **kw)

            return self._proxy_to_logger(name, event.format(*args), **kw)

        meth.__name__ = name

        return meth

    meths: dict[str, Any] = {}
    for lvl, name in LEVEL_TO_NAME.items():
        meths[name] = make_method(lvl)

    meths["exception"] = exception
    meths["fatal"] = _fatal
    meths["msg"] = meths["info"]

    return type(
        f"BoundLoggerFilteringAt{LEVEL_TO_NAME.get(min_level, 'Notset').capitalize()}",
        (_BoundLoggerBase,),
        meths,
    )


# Pre-create all possible filters to make them pickleable.
BoundLoggerFilteringAtNotset = _make_filtering_bound_logger(logging.NOTSET)
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
    logging.NOTSET: BoundLoggerFilteringAtNotset,
}

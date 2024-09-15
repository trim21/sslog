from __future__ import annotations

import logging
from typing import Any, Callable

from structlog import BoundLoggerBase
from structlog._log_levels import LEVEL_TO_NAME
from structlog.typing import FilteringBoundLogger


def _nop(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    return None


def exception(self: Any, event: str, *args: Any, **kw: Any) -> Any:
    kw.setdefault("exc_info", True)

    return self.error(event, *args, **kw)


def make_filtering_bound_logger(min_level: int) -> type[FilteringBoundLogger]:
    return LEVEL_TO_FILTERING_LOGGER[min_level]


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

    def log(self: Any, level: int, event: str, *args: Any, **kw: Any) -> Any:
        if level < min_level:
            return None
        name = LEVEL_TO_NAME[level]

        if not args:
            return self._proxy_to_logger(name, event, **kw)

        return self._proxy_to_logger(name, event.format(*args), **kw)

    meths: dict[str, Any] = {"log": log}
    for lvl, name in LEVEL_TO_NAME.items():
        meths[name] = make_method(lvl)

    meths["exception"] = exception
    meths["fatal"] = meths["error"]
    meths["warn"] = meths["warning"]
    meths["msg"] = meths["info"]

    return type(
        f"BoundLoggerFilteringAt{LEVEL_TO_NAME.get(min_level, 'Notset').capitalize()}",
        (BoundLoggerBase,),
        meths,
    )


# Pre-create all possible filters to make them pickleable.
BoundLoggerFilteringAtNotset = _make_filtering_bound_logger(logging.NOTSET)
BoundLoggerFilteringAtDebug = _make_filtering_bound_logger(logging.DEBUG)
BoundLoggerFilteringAtInfo = _make_filtering_bound_logger(logging.INFO)
BoundLoggerFilteringAtWarning = _make_filtering_bound_logger(logging.WARNING)
BoundLoggerFilteringAtError = _make_filtering_bound_logger(logging.ERROR)
BoundLoggerFilteringAtCritical = _make_filtering_bound_logger(logging.CRITICAL)

LEVEL_TO_FILTERING_LOGGER = {
    logging.CRITICAL: BoundLoggerFilteringAtCritical,
    logging.ERROR: BoundLoggerFilteringAtError,
    logging.WARNING: BoundLoggerFilteringAtWarning,
    logging.INFO: BoundLoggerFilteringAtInfo,
    logging.DEBUG: BoundLoggerFilteringAtDebug,
    logging.NOTSET: BoundLoggerFilteringAtNotset,
}

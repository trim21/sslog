import json
import logging

import structlog

from . import _default
from ._process import add_time


__all__ = ["logger"]

if _default.serialized:
    structlog.configure(
        processors=[
            add_time,
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.CallsiteParameterAdder([
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.LINENO,
                structlog.processors.CallsiteParameter.THREAD,
            ]),
            structlog.dev.set_exc_info,
            structlog.processors.ExceptionRenderer(),
            structlog.processors.EventRenamer("msg"),
            structlog.processors.JSONRenderer(json.dumps, default=str),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

else:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f", utc=False, key="time"),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )

logger: structlog.stdlib.BoundLogger = structlog.get_logger()

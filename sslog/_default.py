from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from os import environ
from typing import Any, TypeVar


T = TypeVar("T")


def env(key: str, typ: Callable[[Any], T], default=None) -> T:
    if key not in environ:
        return default

    val = environ[key]

    if typ is str:
        return typ(val)
    if typ is bool:
        if val.lower() in ["1", "true", "yes", "y", "ok", "on"]:
            return typ(True)
        if val.lower() in ["0", "false", "no", "n", "nok", "off"]:
            return typ(False)
        raise ValueError(
            "Invalid environment variable '%s' (expected a boolean): '%s'" % (key, val)
        )
    if typ is int:
        try:
            return typ(val)
        except ValueError:
            raise ValueError(
                "Invalid environment variable '%s' (expected an integer): '%s'"
                % (key, val)
            ) from None
    raise ValueError("The requested type '%r' is not supported" % typ)


use_json: bool = env("SSLOG_JSON", bool, False)
json_level: str = env("SSLOG_JSON_LEVEL", str, default="INFO")
text_level: str = env("SSLOG_TEXT_LEVEL", str, default="NOTSET")

if sys.version_info >= (3, 11):
    LOGGING_LEVELS = logging.getLevelNamesMapping()
else:
    LOGGING_LEVELS = {
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.FATAL,
        "ERROR": logging.ERROR,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

if json_level.upper() not in LOGGING_LEVELS:
    raise ValueError(
        f"SSLOG_JSON_LEVEL={json_level!r} is not valid default logging level, only allow one of {list(LOGGING_LEVELS.keys())}"
    )

if text_level.upper() not in LOGGING_LEVELS:
    raise ValueError(
        f"SSLOG_TEXT_LEVEL={json_level!r} is not valid default logging level, only allow one of {list(LOGGING_LEVELS.keys())}"
    )

from __future__ import annotations

import logging
from collections.abc import Callable
from os import environ
from typing import Any, TypeVar, cast, overload

T = TypeVar("T")


@overload
def env(key: str, typ: Callable[[Any], T]) -> T | None: ...


@overload
def env(key: str, typ: Callable[[Any], T], default: T) -> T: ...


def env(key: str, typ: Callable[[Any], T], default: T | None = None) -> T | None:
    if key not in environ:
        return default

    val = environ[key]

    if typ is str:
        return cast(T, val)
    if typ is bool:
        if val.lower() in ["1", "true", "yes", "y", "ok", "on"]:
            return cast(T, True)
        if val.lower() in ["0", "false", "no", "n", "nok", "off"]:
            return cast(T, False)
        raise ValueError(
            "Invalid environment variable '%s' (expected a boolean): '%s'" % (key, val)
        )
    if typ is int:
        try:
            return cast(T, int(val))
        except ValueError:
            raise ValueError(
                "Invalid environment variable '%s' (expected an integer): '%s'" % (key, val)
            ) from None
    raise ValueError("The requested type '%r' is not supported" % typ)


use_json: bool = env("SSLOG_JSON", bool, False)
json_level: str = env("SSLOG_JSON_LEVEL", str, default="INFO")
text_level: str = env("SSLOG_TEXT_LEVEL", str, default="NOTSET")

LEVEL_TRACE = 5

LOGGING_LEVELS = {
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "TRACE": LEVEL_TRACE,
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

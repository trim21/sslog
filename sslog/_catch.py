from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from inspect import isclass, iscoroutinefunction, isgeneratorfunction
from typing import TYPE_CHECKING, TypeVar


if TYPE_CHECKING:
    from sslog import _Logger

T = TypeVar("T", bound=Callable)


class Catcher:
    def __init__(
        self,
        logger: _Logger,
        exc: type[BaseException] | tuple[type[BaseException], ...],
        msg: str,
    ):
        self.logger = logger
        self.exc = exc
        self.msg = msg

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return

        if not issubclass(exc_type, self.exc):
            return True

        self.logger.exception(self.msg or "capture a exception")

        return True

    def __call__(self, function: T) -> T:
        if isclass(function):
            raise TypeError(
                "Invalid object decorated with 'catch()', it must be a function, "
                "not a class (tried to wrap '%s')" % function.__name__
            )

        if iscoroutinefunction(function):

            @wraps(function)
            async def catch_wrapper(*args, **kwargs):
                with self:
                    return await function(*args, **kwargs)

        elif isgeneratorfunction(function):

            @wraps(function)
            def catch_wrapper(*args, **kwargs):
                with self:
                    return (yield from function(*args, **kwargs))

        else:

            @wraps(function)
            def catch_wrapper(*args, **kwargs):
                with self:
                    return function(*args, **kwargs)

        return catch_wrapper

from sys import stderr
from typing import Any


class PrintLogger:
    def msg(self, message: str) -> None:
        """Print *message*."""
        stderr.write(message + "\n")

    log = trace = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class PrintLoggerFactory:
    def __call__(self, *args: Any) -> PrintLogger:
        return PrintLogger()

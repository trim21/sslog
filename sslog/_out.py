from __future__ import annotations

import sys
from typing import Any


class PrintLogger:
    def __init__(self):
        pass

    def msg(self, message: str) -> None:
        """Print *message*."""
        sys.stderr.write(message + "\n")

    log = debug = info = warn = warning = msg
    fatal = failure = err = error = critical = exception = msg


class PrintLoggerFactory:
    def __init__(self):
        pass

    def __call__(self, *args: Any) -> PrintLogger:
        return PrintLogger()

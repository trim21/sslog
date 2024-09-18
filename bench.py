import os

os.environ["SSLOG_JSON"] = "1"

from loguru import logger as loguru_logger
from sslog import logger


loguru_logger.remove()
loguru_logger.add(os.devnull, serialize=True, level="INFO")


def test_sslog_disabled(benchmark):
    benchmark(logger.debug, "hello {}", "world", a=1, b="2")


def test_sslog_enabled(benchmark):
    benchmark(logger.info, "hello {}", "world", a=1, b="2")


def test_loguru_disabled(benchmark):
    benchmark(loguru_logger.debug, "hello {}", "world", a=1, b="2")


def test_loguru_enabled(benchmark):
    benchmark(loguru_logger.info, "hello {}", "world", a=1, b="2")

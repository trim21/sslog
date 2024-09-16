import os

from loguru import logger as loguru_logger
from sslog import logger


loguru_logger.remove()
loguru_logger.add(os.devnull, serialize=True)


def test_sslog(benchmark):
    benchmark(logger.info, "hello")


def test_loguru(benchmark):
    benchmark(loguru_logger.info, "hello")

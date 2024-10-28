from structlog import get_logger

import asyncio

from structlog.contextvars import bind_contextvars

logger = get_logger()


logger.info("hello")


async def task():
    logger.info("hello in task")


async def main():
    bind_contextvars(a=1, b=2)
    await task()


asyncio.run(main())

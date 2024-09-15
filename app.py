import asyncio
import contextlib
import time
from threading import Thread

from sslog import logger


logger.info("hello")
logger.info("hello")

logger.info("hello {}", "world")

logger.bind(a=1).info("hello {}", "2")


@logger.catch()
def catched():
    raise ValueError("failed")


with contextlib.suppress(Exception):
    catched()

with logger.catch():
    raise ValueError("failed")


def w1():
    with logger.contextualize(name="a"):
        time.sleep(2)
        logger.info("should contain name")


def w2():
    time.sleep(1)
    logger.info("should not contain name")


ts = [Thread(target=w1), Thread(target=w2())]

for t in ts:
    t.start()

for t in ts:
    t.join()


async def aw1():
    with logger.contextualize(name="a"):
        logger.info("should contain name")
        await asyncio.sleep(2)


async def aw2():
    await asyncio.sleep(1)
    logger.info("should not contain name")


async def main():
    await asyncio.gather(aw1(), aw2())


asyncio.run(main())

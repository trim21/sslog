import sys

from sslog import logger, InterceptHandler

import logging


logger.trace("hello")
logger.debug("hello")
logger.info("hello")
logger.warning("hello")
logger.error("hello")
logger.fatal("hello")

print("stdlib logging", flush=True, file=sys.stderr)
logging.basicConfig(level=logging.NOTSET, handlers=[InterceptHandler()])

logging.debug("hello 1")
logging.info("hello 1")
logging.warning("hello 1")
logging.error("hello 1")
logging.critical("hello 1")

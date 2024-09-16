from sslog import logger
import loguru


logger.debug("hello {}", "debug")
logger.info("hello {}", "info")
logger.warn("hello {}", "warn")
logger.warning("hello {}", "warning")
logger.error("hello {}", "error")
logger.fatal("hello {}", "fatal")
logger.critical("hello {}", "critical")

logger.bind(a=1).info("hello {}", "2")


loguru.logger.info("hello")

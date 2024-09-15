from sslog import logger

logger.info("hello")
logger.info("hello")

logger.info("hello {}", "world")

logger.bind(a=1).info("hello {}", "2")

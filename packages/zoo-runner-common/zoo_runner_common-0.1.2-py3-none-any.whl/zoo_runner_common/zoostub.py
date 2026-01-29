from loguru import logger


class ZooStub:
    def __init__(self):
        self.SERVICE_ACCEPTED = 0
        self.SERVICE_STARTED = 1
        self.SERVICE_PAUSED = 2
        self.SERVICE_SUCCEEDED = 3
        self.SERVICE_FAILED = 4
        self.SERVICE_PAUSED = 5
        self.SERVICE_DEPLOYED = 6
        self.SERVICE_UNDEPLOYED = 7

    def update_status(self, conf, progress):
        print(f"Status {progress}")

    def _(self, message):
        print(f"invoked _ with {message}")

    def trace(self, message):
        logger.trace(message)

    def debug(self, message):
        logger.debug(message)

    def info(self, message):
        logger.info(message)

    def success(self, message):
        logger.success(message)

    def warning(self, message):
        logger.warning(message)

    def error(self, message):
        logger.error(message)

    def critical(self, message):
        logger.critical(message)

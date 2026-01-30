from locker.logger import Logger


class TestLogger(object):
    message = "This is the test log message"

    def test_debug(self):
        logger = Logger(log_level="debug")
        logger.debug(msg=self.message)

    def test_info(self):
        logger = Logger(log_level="info")
        logger.info(msg=self.message)

    def test_warning(self):
        logger = Logger(log_level="warning")
        logger.warning(msg=self.message)

    def test_error(self):
        logger = Logger(log_level="error")
        logger.error(trace=self.message)

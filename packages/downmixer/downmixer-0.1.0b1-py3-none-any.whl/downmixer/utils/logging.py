from __future__ import annotations

from logging import Logger

from downmixer.types import LoggerLike


class LoggerWrapper(LoggerLike):
    def __init__(self, logger: Logger):
        self.logger = logger

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg, exc_info=None):
        self.logger.error(msg, exc_info=exc_info)


class ConsoleLogger(LoggerLike):
    def debug(self, msg):
        print(msg)

    def info(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg, exc_info=None):
        print(msg)

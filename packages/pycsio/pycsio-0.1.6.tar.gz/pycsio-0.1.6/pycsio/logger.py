import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress
from rich.highlighter import NullHighlighter

class Mylogger:
    def __init__(self) -> None:
        self.logger = logging.getLogger("MyLogger")
        self.logger.setLevel(logging.DEBUG)
        self.loggerfile=logging.getLogger("MyLoggerFile")
        self.loggerfile.setLevel(logging.DEBUG)

        handler = RotatingFileHandler("app_log.log", maxBytes=5*1024*1024, encoding='utf-8')
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

        self.loggerfile.addHandler(handler)

        rich_handler = RichHandler()
        rich_handler.setLevel(logging.NOTSET)
        rich_handler.setFormatter(logging.Formatter("%(message)s",datefmt="%Y-%m-%d %H:%M:%S"))
        rich_handler.highlighter=NullHighlighter()
        rich_handler.rich_tracebacks=True
        

        self.logger.addHandler(handler)
        self.logger.addHandler(rich_handler)
    def debug(self, message):
        """记录调试日志"""
        self.logger.debug(message)

    def info(self, message):
        """记录信息日志"""
        self.logger.info(message)

    def error(self, message):
        """记录错误日志"""
        self.logger.error(message)

    def warn(self, message):
        """记录警告日志"""
        self.logger.warning(message)
from .base import BaseLogger
from .cli import CLILogger
from .devnull import DevNullLogger

def logger() -> BaseLogger:
    if BaseLogger.current_logger is None:
        BaseLogger.current_logger = CLILogger()
    return BaseLogger.current_logger

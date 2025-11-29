import logging
import sys
from logging import Formatter, Logger, StreamHandler

from scheduler_service.config import Config

# Define log colors
COLORS = {
    'DEBUG': '\033[36m',  # Cyan
    'INFO': '\033[32m',   # Green
    'WARNING': '\033[33m',  # Yellow
    'ERROR': '\033[31m',    # Red
    'CRITICAL': '\033[41m\033[37m',  # Red background white text
    'RESET': '\033[0m'      # Reset color
}


class ColoredFormatter(Formatter):
    """Colored log formatter"""

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        # Save original message format
        original_fmt = self._fmt

        # Add color based on log level
        levelname = record.levelname
        if levelname in COLORS:
            # Modify message format, add color
            self._fmt = f"{COLORS[levelname]}{original_fmt}{COLORS['RESET']}"

        # Format log record
        result = super().format(record)

        # Restore original format
        self._fmt = original_fmt

        return result


def get_logger(name: str = 'scheduler-service', level: int = None) -> Logger:
    """
    Get configured logger

    Args:
        name: Logger name, default 'scheduler-service'
        level: Log level, read from Config if None

    Returns:
        Configured Logger instance
    """
    # Determine log level
    if level is None:
        level = Config.LOG_LEVEL

    # Create logger
    logger_instance = logging.getLogger(name)
    logger_instance.setLevel(level)

    # Avoid adding duplicate handlers
    if not logger_instance.handlers:
        # Create handler, output to console
        stream_handler = StreamHandler(sys.stdout)
        stream_handler.setLevel(level)  # Use correct level value now

        # Create colored formatter
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Set formatter for handler
        stream_handler.setFormatter(formatter)

        # Add handler to logger
        logger_instance.addHandler(stream_handler)

    return logger_instance


# Create default logger instance
logger = get_logger()

"""Logging configuration for NorthServing."""

import logging
import sys
from typing import Optional

import colorama

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    COLORS = {
        "DEBUG": colorama.Fore.CYAN,
        "INFO": colorama.Fore.GREEN,
        "WARNING": colorama.Fore.YELLOW,
        "ERROR": colorama.Fore.RED,
        "CRITICAL": colorama.Fore.RED + colorama.Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Save original levelname
        original_levelname = record.levelname

        # Add color to levelname
        color = self.COLORS.get(record.levelname, "")
        if color:
            record.levelname = f"{color}{record.levelname}{colorama.Style.RESET_ALL}"

        # Format the message
        result = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return result


def setup_logger(name: str = "northserve", level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    formatter = ColoredFormatter(
        fmt="%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to 'northserve')

    Returns:
        Logger instance
    """
    if name is None:
        name = "northserve"

    logger = logging.getLogger(name)

    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        setup_logger(name)

    return logger


# Create default logger
logger = setup_logger()



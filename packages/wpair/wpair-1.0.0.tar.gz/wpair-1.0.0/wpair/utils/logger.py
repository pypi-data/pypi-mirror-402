"""Logging configuration."""

import logging
import sys
from loguru import logger


def setup_logger(level: str = "INFO"):
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    # Remove default logger
    logger.remove()

    # Add console logger with formatting
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # Optionally add file logger
    logger.add(
        "wpair.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG"
    )


# Setup default logging configuration
setup_logger()

"""
Centralized logging configuration.

Provides a consistent logger across the whole application.
"""

import logging
import sys
from config.settings import settings


def get_logger(name: str = "eleva") -> logging.Logger:
    """
    Return a configured logger.

    Usage:
        from config import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times (important when reloading modules)
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level.upper())

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(settings.log_level.upper())

    # Clean and readable format
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to the root logger (avoids duplicate logs)
    logger.propagate = False

    return logger

"""
Centralized logging configuration.

Provides a consistent logger across the whole application.
"""

import logging
import sys
import os
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

    # Format commun pour les logs
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console handler (ce que tu avais déjà)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level.upper())
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File handler (NOUVEAU : écrit dans logs/eleva.log)
    os.makedirs("logs", exist_ok=True) # Crée le dossier 'logs' s'il n'existe pas
    file_handler = logging.FileHandler("logs/eleva.log", encoding="utf-8")
    file_handler.setLevel(settings.log_level.upper())
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to the root logger (avoids duplicate logs)
    logger.propagate = False

    return logger
"""
config package

Expose les objets de configuration principaux pour un import simple :
    from config import settings, get_logger
"""

from config.settings import settings
from config.logging import get_logger

__all__ = ["settings", "get_logger"]

"""
services package – Deterministic marketing analytics.

No LLM here. Pure calculations (pandas / pure Python).
"""

from services.rfm import compute_rfm
from services.metrics import compute_core_metrics

__all__ = ["compute_rfm", "compute_core_metrics"]
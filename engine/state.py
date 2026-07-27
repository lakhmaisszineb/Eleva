"""
State definition for the Decision Engine.

This will later become the LangGraph state.
For now it is a simple Pydantic model (already defined in core.models).
"""

from core.models import DecisionState

# Re-export for convenience
__all__ = ["DecisionState"]
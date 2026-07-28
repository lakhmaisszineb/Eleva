"""
llm package – Abstraction over the language model (Groq).
"""

from llm.groq_client import get_llm, chat

__all__ = ["get_llm", "chat"]
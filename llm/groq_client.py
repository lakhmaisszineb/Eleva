"""
Groq client wrapper.

Uses llama-3.3-70b-versatile by default.
Provides a simple chat() helper that returns clean text.
"""

from typing import List, Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from config import settings, get_logger

logger = get_logger(__name__)

_llm_instance = None


def get_llm() -> ChatGroq:
    """
    Return a singleton ChatGroq instance.
    """
    global _llm_instance
    if _llm_instance is None:
        if not settings.groq_api_key or settings.groq_api_key.startswith("your_"):
            raise ValueError(
                "GROQ_API_KEY is missing or invalid. "
                "Set it in your .env file."
            )
        _llm_instance = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.3,          # low temperature = more deterministic
            max_tokens=2048,
        )
        logger.info(f"Groq LLM initialized (model={settings.groq_model})")
    return _llm_instance


def chat(
    system_prompt: str,
    user_prompt: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Simple chat helper.

    Args:
        system_prompt: role + instructions
        user_prompt: the actual question / data
        history: optional list of {"role": "user"|"assistant", "content": "..."}

    Returns:
        The assistant response as plain text.
    """
    llm = get_llm()

    messages = [SystemMessage(content=system_prompt)]

    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_prompt))

    logger.debug("Sending request to Groq...")
    response = llm.invoke(messages)
    content = response.content.strip()
    logger.debug(f"Groq response length: {len(content)} chars")
    return content
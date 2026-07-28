"""
Plan node – Step 6 (LLM-augmented).
"""

from typing import List
import json
import uuid
import re

from core.models import DecisionState, Strategy
from llm.groq_client import chat
from llm.prompts import PLAN_SYSTEM, PLAN_USER_TEMPLATE
from config import get_logger

logger = get_logger(__name__)


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    return json.loads(text)


def plan_node(state: DecisionState) -> DecisionState:
    logger.info("[Plan] Building strategies (LLM)")

    hypotheses_block = "\n".join(
        f"- {h.statement} (confidence: {h.confidence})"
        for h in state.hypotheses
    )
    playbooks_block = "\n".join(
        f"- {pb['technique']}" for pb in state.retrieved_playbooks
    ) or "Aucun"

    user_prompt = PLAN_USER_TEMPLATE.format(
        hypotheses_block=hypotheses_block,
        playbooks_block=playbooks_block,
    )

    strategies: List[Strategy] = []

    try:
        raw = chat(PLAN_SYSTEM, user_prompt)
        data = _extract_json(raw)

        for s in data.get("strategies", []):
            strategies.append(
                Strategy(
                    id=str(uuid.uuid4())[:8],
                    name=s.get("name", "Stratégie"),
                    description=s.get("description", ""),
                    related_hypothesis_ids=[h.id for h in state.hypotheses[:1]],
                    recommended_playbooks=s.get("playbooks", []),
                    expected_impact=s.get("expected_impact"),
                    effort=s.get("effort"),
                    risks=s.get("main_risks", []),
                )
            )
        logger.info(f"[Plan] LLM produced {len(strategies)} strategy(ies)")

    except Exception as e:
        logger.error(f"[Plan] LLM failed ({e}) – fallback")
        for hyp in state.hypotheses:
            strategies.append(
                Strategy(
                    id=str(uuid.uuid4())[:8],
                    name=f"Stratégie liée",
                    description=hyp.statement,
                    related_hypothesis_ids=[hyp.id],
                    recommended_playbooks=[],
                    expected_impact="Moyen",
                    effort="Moyen",
                    risks=[],
                )
            )

    state.strategies = strategies
    state.current_step = "decide"
    return state
"""
Recommend node – Step 8 (LLM-augmented).
"""

from typing import List
import json
import uuid
import re
from datetime import datetime

from core.models import (
    DecisionState,
    Recommendation,
    Priority,
    RecommendationStatus,
)
from llm.groq_client import chat
from llm.prompts import RECOMMEND_SYSTEM, RECOMMEND_USER_TEMPLATE
from config import get_logger

logger = get_logger(__name__)


def _extract_json(text: str) -> dict:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    return json.loads(text)


def recommend_node(state: DecisionState) -> DecisionState:
    logger.info("[Recommend] Building final recommendations (LLM)")

    strategies_block = "\n\n".join(
        f"### {s.name}\n{s.description}\nImpact: {s.expected_impact} | Effort: {s.effort}\n"
        f"Playbooks: {', '.join(s.recommended_playbooks)}"
        for s in state.strategies
    )

    ctx = state.company_context
    user_prompt = RECOMMEND_USER_TEMPLATE.format(
        company_name=ctx.name if ctx else "Unknown",
        industry=ctx.industry if ctx else "Unknown",
        question=state.request.question,
        strategies_block=strategies_block,
        max_recommendations=state.request.max_recommendations,
    )

    recommendations: List[Recommendation] = []

    try:
        raw = chat(RECOMMEND_SYSTEM, user_prompt)
        data = _extract_json(raw)

        priority_map = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
            "critical": Priority.CRITICAL,
        }

        for r in data.get("recommendations", []):
            recommendations.append(
                Recommendation(
                    id=str(uuid.uuid4())[:8],
                    company_id=state.request.company_id,
                    title=r.get("title", "Recommandation"),
                    summary=r.get("summary", ""),
                    justification=r.get("justification", ""),
                    priority=priority_map.get(r.get("priority", "medium").lower(), Priority.MEDIUM),
                    strategies=state.strategies[:1],
                    expected_outcomes=r.get("expected_outcomes", []),
                    next_steps=r.get("next_steps", []),
                    status=RecommendationStatus.PENDING_APPROVAL,
                    created_at=datetime.utcnow(),
                )
            )
        logger.info(f"[Recommend] LLM produced {len(recommendations)} recommendation(s)")

    except Exception as e:
        logger.error(f"[Recommend] LLM failed ({e}) – fallback")
        for s in state.strategies[: state.request.max_recommendations]:
            recommendations.append(
                Recommendation(
                    id=str(uuid.uuid4())[:8],
                    company_id=state.request.company_id,
                    title=s.name,
                    summary=s.description,
                    justification="Généré en mode fallback (LLM indisponible).",
                    priority=Priority.MEDIUM,
                    strategies=[s],
                    expected_outcomes=[],
                    next_steps=["Review and approve this recommendation"],
                    status=RecommendationStatus.PENDING_APPROVAL,
                    created_at=datetime.utcnow(),
                )
            )

    state.recommendations = recommendations[: state.request.max_recommendations]
    state.current_step = "done"
    return state
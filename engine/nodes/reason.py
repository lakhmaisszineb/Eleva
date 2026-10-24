"""
Reason node – Step 5 (LLM-augmented).
"""

from typing import List
import json
import uuid
import re

from core.models import DecisionState, Hypothesis
from llm.groq_client import chat
from llm.prompts import REASON_SYSTEM, REASON_USER_TEMPLATE
from config import get_logger

logger = get_logger(__name__)


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response (handles markdown fences)."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1)
    return json.loads(text)


def reason_node(state: DecisionState) -> DecisionState:
    logger.info("[Reason] Generating hypotheses (LLM)")

    # Build context blocks
    issues_block = "\n".join(
        f"- [{i.priority.value}] {i.type.value}: {i.title} — {i.description}"
        for i in state.detected_issues
    )
    playbooks_block = "\n".join(
        f"- {pb['technique']} (for issue: {pb['issue_title']})"
        for pb in state.retrieved_playbooks
    ) or "Aucun playbook spécifique"

    ctx = state.company_context
    user_prompt = REASON_USER_TEMPLATE.format(
        company_name=ctx.name if ctx else "Unknown",
        industry=ctx.industry if ctx else "Unknown",
        current_focus=ctx.current_focus if ctx else "N/A",
        goals=", ".join(ctx.goals) if ctx and ctx.goals else "N/A",
        issues_block=issues_block,
        playbooks_block=playbooks_block,
        question=state.request.question,
    )

    hypotheses: List[Hypothesis] = []

    try:
        raw = chat(REASON_SYSTEM, user_prompt)
        data = _extract_json(raw)

        for h in data.get("hypotheses", []):
            # Match issue by title (approximate)
            # Match issue by title when the LLM provides an issue title.
            related_ids = []
            issue_title = str(h.get("issue_title") or "").strip().lower()

            if issue_title:
                for issue in state.detected_issues:
                    issue_title_candidate = issue.title.lower()

                    if (
                        issue_title_candidate in issue_title
                        or issue_title in issue_title_candidate
                    ):
                        related_ids.append(issue.id)
            raw_confidence = h.get("confidence")
            try:
                confidence = (
                    float(raw_confidence)
                    if raw_confidence is not None
                    else 0.7
                )
            except (TypeError, ValueError):
                confidence = 0.7
            hypotheses.append(
                Hypothesis(
                    id=str(uuid.uuid4())[:8],
                    statement=h.get("statement", ""),
                    supporting_evidence=[],
                    confidence=confidence,
                    related_issue_ids=related_ids or (
                        [state.detected_issues[0].id] if state.detected_issues else []
                    ),
                )
            )
        logger.info(f"[Reason] LLM produced {len(hypotheses)} hypothesis(es)")

    except Exception as e:
        logger.error(f"[Reason] LLM failed ({e}) – falling back to deterministic mode")
        # Fallback simple
        for issue in state.detected_issues:
            related_pbs = [
                pb["technique"] for pb in state.retrieved_playbooks
                if pb.get("issue_id") == issue.id
            ]
            hypotheses.append(
                Hypothesis(
                    id=str(uuid.uuid4())[:8],
                    statement=(
                        f"L'issue '{issue.title}' peut être traitée via : "
                        f"{', '.join(related_pbs) if related_pbs else 'bonnes pratiques générales'}."
                    ),
                    supporting_evidence=issue.evidence,
                    confidence=0.6,
                    related_issue_ids=[issue.id],
                )
            )

    state.hypotheses = hypotheses
    state.current_step = "plan"
    return state
"""
Retrieve node – Step 4 of the Decision Engine.

Consults the Knowledge Base (RAG) to find relevant marketing playbooks
for the detected issues.
"""

from typing import List, Dict, Any

from core.models import DecisionState
from knowledge.rag import KnowledgeBase
from config import get_logger

logger = get_logger(__name__)


def retrieve_node(state: DecisionState) -> DecisionState:
    """
    For each detected issue, retrieve the most relevant playbooks.
    """
    logger.info("[Retrieve] Consulting Knowledge Base")

    if not state.detected_issues:
        logger.warning("[Retrieve] No detected issues – skipping retrieval")
        state.current_step = "reason"
        return state

    kb = KnowledgeBase()

    # Make sure playbooks are indexed
    count = kb.index_playbooks()
    logger.info(f"[Retrieve] Knowledge base contains {count} playbook(s)")

    all_retrieved: List[Dict[str, Any]] = []
    seen_techniques = set()

    for issue in state.detected_issues:
        # Build a focused query from the issue
        query = f"{issue.title}. {issue.description}"
        logger.info(f"[Retrieve] Querying for: {issue.title}")

        results = kb.retrieve(query, n_results=2)

        for r in results:
            technique = r["metadata"].get("technique", "Unknown")
            if technique not in seen_techniques:
                seen_techniques.add(technique)
                all_retrieved.append({
                    "issue_id": issue.id,
                    "issue_title": issue.title,
                    "technique": technique,
                    "content": r["content"],
                    "distance": r["distance"],
                })
                logger.info(f"  → Matched playbook: {technique}")

    state.retrieved_playbooks = all_retrieved
    state.current_step = "reason"

    logger.info(f"[Retrieve] Retrieved {len(all_retrieved)} unique playbook(s)")
    return state
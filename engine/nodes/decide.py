"""
Decide node – Step 7.

Selects the best strategies (simple priority-based selection for V1).
"""

from core.models import DecisionState, Priority
from config import get_logger

logger = get_logger(__name__)


def decide_node(state: DecisionState) -> DecisionState:
    logger.info("[Decide] Selecting best strategies")

    # Sort issues by priority (CRITICAL > HIGH > MEDIUM > LOW)
    priority_order = {
        Priority.CRITICAL: 0,
        Priority.HIGH: 1,
        Priority.MEDIUM: 2,
        Priority.LOW: 3,
    }

    sorted_issues = sorted(
        state.detected_issues,
        key=lambda i: priority_order.get(i.priority, 99)
    )

    # Keep strategies linked to the top issues (max 3)
    top_issue_ids = {i.id for i in sorted_issues[:3]}

    selected = []
    for strategy in state.strategies:
        # Check if strategy is linked to a top issue via its hypotheses
        for hyp in state.hypotheses:
            if hyp.id in strategy.related_hypothesis_ids:
                if any(iid in top_issue_ids for iid in hyp.related_issue_ids):
                    selected.append(strategy)
                    break

    # Fallback: keep first 3 strategies if nothing selected
    if not selected:
        selected = state.strategies[:3]

    state.strategies = selected  # keep only selected ones
    state.current_step = "recommend"
    logger.info(f"[Decide] Selected {len(selected)} strategy(ies)")
    return state
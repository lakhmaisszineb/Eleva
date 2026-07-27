"""
Understand node – Step 1 of the Decision Engine.

Loads the company context and prepares the initial state.
"""

from core.models import DecisionState, AnalysisRequest
from data.company_store import CompanyStore
from config import get_logger

logger = get_logger(__name__)


def understand_node(state: DecisionState) -> DecisionState:
    """
    Load company context from the CompanyStore.
    """
    logger.info(f"[Understand] Loading context for company_id={state.request.company_id}")

    store = CompanyStore()
    try:
        context = store.get_company_context(state.request.company_id)
        state.company_context = context
        state.current_step = "observe"
        logger.info(f"[Understand] Company loaded: {context.name} ({context.industry})")
    except Exception as e:
        logger.error(f"[Understand] Failed: {e}")
        state.errors.append(f"Understand failed: {str(e)}")

    return state
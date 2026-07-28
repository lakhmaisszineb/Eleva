"""
DecisionEngine – Orchestrates the full decision cycle (On Demand mode).

Current version: sequential and synchronous.
Later: will be converted to LangGraph.
"""

from core.models import AnalysisRequest, DecisionState
from engine.nodes.understand import understand_node
from engine.nodes.observe import observe_node
from engine.nodes.detect import detect_node
from engine.nodes.retrieve import retrieve_node
from engine.nodes.reason import reason_node
from engine.nodes.plan import plan_node
from engine.nodes.decide import decide_node
from engine.nodes.recommend import recommend_node
from config import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    """
    Main entry point of Eleva.
    """

    def __init__(self):
        logger.info("DecisionEngine initialized")

    def run(self, request: AnalysisRequest) -> DecisionState:
        """
        Execute the full decision cycle for a given request.
        """
        logger.info(f"Starting decision cycle for company={request.company_id}")
        logger.info(f"Question: {request.question}")

        state = DecisionState(request=request)

        # ----- Full Pipeline (V1 – sequential) -----
        state = understand_node(state)
        if state.errors:
            return state

        state = observe_node(state)
        if state.errors:
            return state

        state = detect_node(state)
        if state.errors:
            return state

        state = retrieve_node(state)
        if state.errors:
            return state

        state = reason_node(state)
        if state.errors:
            return state

        state = plan_node(state)
        if state.errors:
            return state

        state = decide_node(state)
        if state.errors:
            return state

        state = recommend_node(state)
        if state.errors:
            return state

        logger.info("Decision cycle finished successfully")
        return state
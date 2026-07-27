"""
DecisionEngine – Orchestrates the full decision cycle (On Demand mode).

Current version: sequential and synchronous.
Later: will be converted to LangGraph.
"""

from core.models import AnalysisRequest, DecisionState, Recommendation
from engine.nodes.understand import understand_node
from engine.nodes.observe import observe_node
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
        Execute the decision cycle for a given request.
        """
        logger.info(f"Starting decision cycle for company={request.company_id}")
        logger.info(f"Question: {request.question}")

        # Initialize state
        state = DecisionState(request=request)

        # ----- Pipeline (V1 – sequential) -----
        state = understand_node(state)
        if state.errors:
            return state

        state = observe_node(state)
        if state.errors:
            return state

        # TODO: next nodes
        # state = detect_node(state)
        # state = retrieve_node(state)
        # state = reason_node(state)
        # state = plan_node(state)
        # state = decide_node(state)
        # state = recommend_node(state)

        logger.info("Decision cycle finished (partial – Observe only for now)")
        return state
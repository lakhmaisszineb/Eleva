"""
Detect node – Step 3 of the Decision Engine.

Analyzes the Observation and produces a list of DetectedIssue
(problems and opportunities) with priority and evidence.
"""

from typing import List
import uuid

from core.models import (
    DecisionState,
    DetectedIssue,
    IssueType,
    Priority,
)
from config import get_logger

logger = get_logger(__name__)


def detect_node(state: DecisionState) -> DecisionState:
    """
    Detect problems and opportunities from the observation.
    """
    logger.info("[Detect] Starting issue detection")

    if not state.observation:
        state.errors.append("Detect failed: no observation available")
        return state

    obs = state.observation
    issues: List[DetectedIssue] = []

    # Helper to create an issue quickly
    def add_issue(
        type_: IssueType,
        title: str,
        description: str,
        priority: Priority,
        related_kpis: List[str],
        evidence: List[str],
    ):
        issues.append(
            DetectedIssue(
                id=str(uuid.uuid4())[:8],
                type=type_,
                title=title,
                description=description,
                priority=priority,
                related_kpis=related_kpis,
                evidence=evidence,
            )
        )

    # ------------------------------------------------------------------
    # Rules based on observation (deterministic for V1)
    # ------------------------------------------------------------------

    # 1. Cart abandonment
    abandonment_kpi = next((k for k in obs.kpis if k.name == "cart_abandonment_rate"), None)
    abandoned_count = next((k for k in obs.kpis if k.name == "abandoned_orders"), None)

    if abandonment_kpi and abandonment_kpi.value >= 0.25:
        add_issue(
            type_=IssueType.PROBLEM,
            title="High cart abandonment rate",
            description=(
                f"The cart abandonment rate is {abandonment_kpi.value:.0%}. "
                "This is above the acceptable threshold and represents lost revenue."
            ),
            priority=Priority.HIGH,
            related_kpis=["cart_abandonment_rate", "abandoned_orders"],
            evidence=[
                f"Abandonment rate: {abandonment_kpi.value}",
                f"Number of abandoned orders: {abandoned_count.value if abandoned_count else 'N/A'}",
            ],
        )

    # 2. At Risk customers
    at_risk_seg = next((s for s in obs.segments if s.name == "At Risk"), None)
    if at_risk_seg and at_risk_seg.size > 0:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Customers at risk of churning",
            description=(
                f"{at_risk_seg.size} customer(s) ({at_risk_seg.percentage}%) are in the 'At Risk' segment. "
                "They need proactive retention actions."
            ),
            priority=Priority.HIGH if at_risk_seg.percentage >= 20 else Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"At Risk segment size: {at_risk_seg.size}",
                f"Percentage of customer base: {at_risk_seg.percentage}%",
            ],
        )

    # 3. High churn risk scores
    high_churn_insights = [i for i in obs.raw_insights if "high churn risk score" in i.lower()]
    if high_churn_insights:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Elevated churn risk scores detected",
            description=(
                "Several customers have a churn risk score ≥ 0.7. "
                "Immediate win-back or retention actions should be considered."
            ),
            priority=Priority.HIGH,
            related_kpis=[],
            evidence=high_churn_insights,
        )

    # 4. Low ROI campaigns
    low_roi_insights = [i for i in obs.raw_insights if "low roi campaigns" in i.lower()]
    if low_roi_insights:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Underperforming campaigns",
            description=(
                "One or more campaigns show low ROI. "
                "They should be reviewed, paused, or redesigned."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=low_roi_insights,
        )

    # 5. Opportunity – VIP segment exists
    vip_seg = next((s for s in obs.segments if s.name == "VIP"), None)
    if vip_seg and vip_seg.size > 0:
        add_issue(
            type_=IssueType.OPPORTUNITY,
            title="Leverage VIP customers",
            description=(
                f"There are {vip_seg.size} VIP customers ({vip_seg.percentage}% of the base). "
                "They can be activated for higher AOV, referrals, or exclusive offers."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"VIP segment size: {vip_seg.size}",
                f"Percentage: {vip_seg.percentage}%",
            ],
        )

    # 6. Opportunity – New customers
    new_seg = next((s for s in obs.segments if s.name == "New"), None)
    if new_seg and new_seg.size > 0:
        add_issue(
            type_=IssueType.OPPORTUNITY,
            title="Convert new customers into second purchase",
            description=(
                f"{new_seg.size} new customer(s) can be nurtured with a strong welcome / second-purchase campaign."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=[f"New segment size: {new_seg.size}"],
        )

    # ------------------------------------------------------------------
    # Save results
    # ------------------------------------------------------------------
    state.detected_issues = issues
    state.current_step = "retrieve"

    logger.info(f"[Detect] Found {len(issues)} issue(s)")
    for issue in issues:
        logger.info(f"  → [{issue.priority.value.upper()}] {issue.type.value}: {issue.title}")

    return state
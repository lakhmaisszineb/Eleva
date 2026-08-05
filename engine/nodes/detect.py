"""
Detect node – Step 3 of the Decision Engine.
Issues en français, basées sur Observation (RFM + KPIs).
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
    logger.info("[Detect] Starting issue detection")

    if not state.observation:
        state.errors.append("Detect failed: no observation available")
        return state

    obs = state.observation
    issues: List[DetectedIssue] = []

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

    def kpi_val(name: str):
        for k in obs.kpis:
            if k.name == name:
                return k.value
        return None

    def seg(name: str):
        for s in obs.segments:
            if s.name == name:
                return s
        return None

    # ----- Problèmes -----

    abandonment = kpi_val("cart_abandonment_rate")
    abandoned_count = kpi_val("abandoned_orders")
    if abandonment is not None and float(abandonment) >= 0.25:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Taux d'abandon de panier élevé",
            description=(
                f"Le taux d'abandon de panier est de {float(abandonment):.0%}. "
                "Cela représente un manque à gagner important."
            ),
            priority=Priority.HIGH,
            related_kpis=["cart_abandonment_rate", "abandoned_orders"],
            evidence=[
                f"Taux d'abandon : {abandonment}",
                f"Nombre de paniers abandonnés : {abandoned_count}",
            ],
        )

    at_risk = seg("At Risk")
    if at_risk and at_risk.size > 0:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Clients à risque de churn (RFM)",
            description=(
                f"{at_risk.size} client(s) ({at_risk.percentage} %) sont classés "
                "« At Risk » par l'analyse RFM. Des actions de rétention sont nécessaires."
            ),
            priority=Priority.HIGH if at_risk.percentage >= 15 else Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"Segment RFM « At Risk » : {at_risk.size} clients ({at_risk.percentage} %)",
            ],
        )

    lost = seg("Lost / Churned")
    if lost and lost.size > 0:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Clients perdus ou churnés (RFM)",
            description=(
                f"{lost.size} client(s) ({lost.percentage} %) sont classés "
                "« Lost / Churned ». Une campagne de réactivation peut être pertinente."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"Segment RFM « Lost / Churned » : {lost.size} clients ({lost.percentage} %)",
            ],
        )

    high_churn = kpi_val("high_churn_risk_count")
    if high_churn is not None and int(high_churn) > 0:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Scores de risque de churn élevés",
            description=(
                f"{high_churn} client(s) ont un score de churn ≥ 0,7. "
                "Une intervention proactive est recommandée."
            ),
            priority=Priority.HIGH,
            related_kpis=["high_churn_risk_count"],
            evidence=[f"high_churn_risk_count = {high_churn}"],
        )

    repeat = kpi_val("repeat_purchase_rate")
    if repeat is not None and float(repeat) < 0.30:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Taux de réachat faible",
            description=(
                f"Le taux de réachat est de {float(repeat):.0%}, ce qui est faible. "
                "Des actions de fidélisation / 2ᵉ commande sont prioritaires."
            ),
            priority=Priority.MEDIUM,
            related_kpis=["repeat_purchase_rate"],
            evidence=[f"repeat_purchase_rate = {repeat}"],
        )

    low_roi_insights = [
        i for i in obs.raw_insights
        if "faible ROI" in i.lower() or "low roi" in i.lower()
    ]
    if low_roi_insights:
        add_issue(
            type_=IssueType.PROBLEM,
            title="Campagnes sous-performantes",
            description="Une ou plusieurs campagnes ont un ROI faible et devraient être revues.",
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=low_roi_insights,
        )

    # ----- Opportunités -----

    champions = seg("Champions")
    if champions and champions.size > 0:
        add_issue(
            type_=IssueType.OPPORTUNITY,
            title="Valoriser les clients Champions (RFM)",
            description=(
                f"{champions.size} client(s) « Champions » ({champions.percentage} %). "
                "Ils peuvent être activés pour du parrainage, des offres exclusives ou de l'upsell."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"Segment RFM « Champions » : {champions.size} ({champions.percentage} %)",
            ],
        )

    new_seg = seg("New / Promising")
    if new_seg and new_seg.size > 0:
        add_issue(
            type_=IssueType.OPPORTUNITY,
            title="Convertir les nouveaux clients / prometteurs",
            description=(
                f"{new_seg.size} client(s) « New / Promising ». "
                "Une campagne de bienvenue / 2ᵉ commande peut les faire progresser."
            ),
            priority=Priority.MEDIUM,
            related_kpis=[],
            evidence=[
                f"Segment RFM « New / Promising » : {new_seg.size} ({new_seg.percentage} %)",
            ],
        )

    state.detected_issues = issues
    state.current_step = "retrieve"

    logger.info(f"[Detect] Found {len(issues)} issue(s)")
    for issue in issues:
        logger.info(f"  → [{issue.priority.value.upper()}] {issue.type.value}: {issue.title}")

    return state
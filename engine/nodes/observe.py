"""
Observe node – Step 2 of the Decision Engine.

Collects company data and computes:
- Core KPIs (via services.metrics)
- RFM segments (via services.rfm)
- Human-readable insights
"""

from datetime import datetime
from typing import List
from collections import Counter

from core.models import (
    DecisionState,
    Observation,
    KPI,
    SegmentSummary,
)
from data.company_store import CompanyStore
from services.metrics import compute_core_metrics
from services.rfm import compute_rfm
from config import get_logger

logger = get_logger(__name__)


def observe_node(state: DecisionState) -> DecisionState:
    """
    Collect and summarize company data.
    Produces a structured Observation object.
    """
    company_id = state.request.company_id
    logger.info(f"[Observe] Starting observation for {company_id}")

    store = CompanyStore()

    try:
        customers = store.get_customers(company_id)
        orders = store.get_orders(company_id)
        campaigns = store.get_campaigns(company_id)

        # ----- Core metrics -----
        metrics = compute_core_metrics(customers, orders, campaigns)

        kpis: List[KPI] = [
            KPI(name="total_customers", value=metrics["total_customers"]),
            KPI(name="total_orders", value=metrics["total_orders"]),
            KPI(name="completed_orders", value=metrics["completed_orders"]),
            KPI(name="abandoned_orders", value=metrics["abandoned_orders"]),
            KPI(
                name="cart_abandonment_rate",
                value=metrics["cart_abandonment_rate"],
                unit="ratio",
            ),
            KPI(
                name="average_order_value",
                value=metrics["average_order_value"],
                unit="currency",
            ),
            KPI(
                name="repeat_purchase_rate",
                value=metrics["repeat_purchase_rate"],
                unit="ratio",
            ),
            KPI(
                name="approx_clv",
                value=metrics["approx_clv"],
                unit="currency",
            ),
            KPI(
                name="high_churn_risk_count",
                value=metrics["high_churn_risk_count"],
            ),
        ]

        # ----- RFM -----
        rfm_results = compute_rfm(customers, orders)
        rfm_counter = Counter(r["rfm_segment"] for r in rfm_results)

        segments: List[SegmentSummary] = []
        total_rfm = len(rfm_results) or 1
        for name, size in rfm_counter.items():
            segments.append(
                SegmentSummary(
                    name=name,
                    size=size,
                    percentage=round(size / total_rfm * 100, 1),
                    key_metrics={},
                )
            )

        # Store RFM details in metadata for explainability
        rfm_summary = {
            "segments": dict(rfm_counter),
            "sample": rfm_results[:5],  # small sample for traceability
        }

        # ----- Insights -----
        insights: List[str] = []

        if metrics["abandoned_orders"] > 0:
            insights.append(
                f"{metrics['abandoned_orders']} panier(s) abandonné(s) "
                f"({metrics['cart_abandonment_rate']:.0%} des commandes)."
            )

        if metrics["high_churn_risk_count"] > 0:
            insights.append(
                f"{metrics['high_churn_risk_count']} client(s) avec un score de churn élevé (≥ 0.7)."
            )

        if metrics["low_roi_campaigns_count"] > 0:
            names = ", ".join(metrics["low_roi_campaign_names"])
            insights.append(f"Campagnes à faible ROI détectées : {names}.")

        at_risk_rfm = rfm_counter.get("At Risk", 0)
        if at_risk_rfm > 0:
            insights.append(
                f"{at_risk_rfm} client(s) classés 'At Risk' par l'analyse RFM."
            )

        lost = rfm_counter.get("Lost / Churned", 0)
        if lost > 0:
            insights.append(
                f"{lost} client(s) classés 'Lost / Churned' par l'analyse RFM."
            )

        champions = rfm_counter.get("Champions", 0)
        if champions > 0:
            insights.append(
                f"{champions} client(s) 'Champions' (fort potentiel de valeur)."
            )

        if metrics["repeat_purchase_rate"] < 0.3:
            insights.append(
                f"Taux de réachat faible ({metrics['repeat_purchase_rate']:.0%})."
            )

        # ----- Build Observation -----
        observation = Observation(
            company_id=company_id,
            observed_at=datetime.utcnow(),
            kpis=kpis,
            segments=segments,
            raw_insights=insights,
            data_sources=["customers.json", "orders.json", "campaigns.json", "rfm", "metrics"],
            metadata={
                "rfm": rfm_summary,
                "metrics": metrics,
            },
        )

        state.observation = observation
        state.current_step = "detect"
        logger.info(
            f"[Observe] Done – {len(kpis)} KPIs, {len(segments)} RFM segments, "
            f"{len(insights)} insights"
        )

    except Exception as e:
        logger.error(f"[Observe] Failed: {e}")
        state.errors.append(f"Observe failed: {str(e)}")

    return state
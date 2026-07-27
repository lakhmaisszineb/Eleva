"""
Observe node – Step 2 of the Decision Engine.

This is where the agent looks at the company's reality:
- Customers
- Orders
- Campaigns
- Simple derived KPIs and insights
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

        # ----- Basic KPIs -----
        kpis: List[KPI] = []

        total_customers = len(customers)
        kpis.append(KPI(name="total_customers", value=total_customers))

        total_orders = len(orders)
        kpis.append(KPI(name="total_orders", value=total_orders))

        completed_orders = [o for o in orders if o.get("status") == "completed"]
        abandoned_orders = [o for o in orders if o.get("status") == "abandoned"]

        kpis.append(KPI(name="completed_orders", value=len(completed_orders)))
        kpis.append(KPI(name="abandoned_orders", value=len(abandoned_orders)))

        if total_orders > 0:
            abandonment_rate = len(abandoned_orders) / total_orders
            kpis.append(KPI(
                name="cart_abandonment_rate",
                value=round(abandonment_rate, 3),
                unit="ratio"
            ))

        # Average order value (completed only)
        if completed_orders:
            aov = sum(o.get("total", 0) for o in completed_orders) / len(completed_orders)
            kpis.append(KPI(name="average_order_value", value=round(aov, 2), unit="currency"))

        # ----- Segments -----
        segment_counter = Counter(c.get("segment", "Unknown") for c in customers)
        segments: List[SegmentSummary] = []
        for name, size in segment_counter.items():
            percentage = (size / total_customers * 100) if total_customers > 0 else 0
            segments.append(SegmentSummary(
                name=name,
                size=size,
                percentage=round(percentage, 1)
            ))

        # ----- Simple insights (human-readable) -----
        insights: List[str] = []

        if abandoned_orders:
            insights.append(
                f"{len(abandoned_orders)} abandoned cart(s) detected "
                f"({round(len(abandoned_orders)/max(total_orders,1)*100, 1)}% of orders)."
            )

        at_risk = [c for c in customers if c.get("segment") == "At Risk"]
        if at_risk:
            insights.append(f"{len(at_risk)} customer(s) currently in 'At Risk' segment.")

        high_churn = [c for c in customers if c.get("churn_risk_score", 0) >= 0.7]
        if high_churn:
            insights.append(f"{len(high_churn)} customer(s) have a high churn risk score (≥ 0.7).")

        low_roi_campaigns = [
            c for c in campaigns
            if c.get("roi") is not None and c.get("roi") < 1.5
        ]
        if low_roi_campaigns:
            names = ", ".join(c.get("name", "Unknown") for c in low_roi_campaigns)
            insights.append(f"Low ROI campaigns detected: {names}")

        # ----- Build Observation -----
        observation = Observation(
            company_id=company_id,
            observed_at=datetime.utcnow(),
            kpis=kpis,
            segments=segments,
            raw_insights=insights,
            data_sources=["customers.json", "orders.json", "campaigns.json"],
        )

        state.observation = observation
        state.current_step = "detect"
        logger.info(f"[Observe] Observation complete – {len(insights)} insight(s) generated")

    except Exception as e:
        logger.error(f"[Observe] Failed: {e}")
        state.errors.append(f"Observe failed: {str(e)}")

    return state
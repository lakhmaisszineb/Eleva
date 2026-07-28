"""
Core marketing metrics computed from customers / orders / campaigns.
"""

from typing import List, Dict, Any, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    return int(_safe_float(value, float(default)))


def compute_core_metrics(
    customers: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    campaigns: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Return a dict of core KPIs.
    Robust to missing / None fields (e.g. after CSV import).
    """
    total_customers = len(customers)
    completed = [o for o in orders if o.get("status") == "completed"]
    abandoned = [o for o in orders if o.get("status") == "abandoned"]
    total_orders = len(orders)

    aov = (
        sum(_safe_float(o.get("total")) for o in completed) / len(completed)
        if completed else 0.0
    )

    abandonment_rate = (
        len(abandoned) / total_orders if total_orders > 0 else 0.0
    )

    # Repeat purchase rate
    orders_per_customer: Dict[str, int] = {}
    for o in completed:
        cid = o.get("customer_id")
        if cid:
            orders_per_customer[cid] = orders_per_customer.get(cid, 0) + 1

    repeat_customers = sum(1 for v in orders_per_customer.values() if v >= 2)
    customers_with_orders = len(orders_per_customer) or 1
    repeat_rate = repeat_customers / customers_with_orders

    # Approx CLV
    clv = (
        sum(_safe_float(c.get("total_spent")) for c in customers) / total_customers
        if total_customers else 0.0
    )

    # High churn risk (None-safe)
    high_churn = [
        c for c in customers
        if _safe_float(c.get("churn_risk_score"), 0.0) >= 0.7
    ]

    # Campaign summary
    low_roi = []
    low_roi_names = []
    for c in campaigns:
        roi = c.get("roi")
        if roi is not None and _safe_float(roi, 999) < 1.5:
            low_roi.append(c)
            low_roi_names.append(c.get("name") or "Unknown")

    return {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "completed_orders": len(completed),
        "abandoned_orders": len(abandoned),
        "cart_abandonment_rate": round(abandonment_rate, 3),
        "average_order_value": round(aov, 2),
        "repeat_purchase_rate": round(repeat_rate, 3),
        "approx_clv": round(clv, 2),
        "high_churn_risk_count": len(high_churn),
        "low_roi_campaigns_count": len(low_roi),
        "low_roi_campaign_names": low_roi_names,
    }
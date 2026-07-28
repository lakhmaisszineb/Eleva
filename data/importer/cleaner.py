"""
Clean and normalize raw row values after column mapping.
"""

from typing import Any, Dict, Optional
import re
from datetime import datetime


STATUS_MAP = {
    "completed": "completed",
    "complete": "completed",
    "paid": "completed",
    "payé": "completed",
    "paye": "completed",
    "livré": "completed",
    "livre": "completed",
    "shipped": "completed",
    "fulfilled": "completed",
    "abandoned": "abandoned",
    "abandonné": "abandoned",
    "abandonne": "abandoned",
    "cart_abandoned": "abandoned",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "annulé": "cancelled",
    "annule": "cancelled",
    "refunded": "refunded",
    "remboursé": "refunded",
    "rembourse": "refunded",
}


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "").replace(",", ".")
    s = re.sub(r"[^\d.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return None


def _to_int(value: Any) -> Optional[int]:
    f = _to_float(value)
    if f is None:
        return None
    return int(f)


def _to_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_date(value: Any) -> Optional[str]:
    """Return ISO date string YYYY-MM-DD if possible."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return None


def _normalize_status(value: Any) -> Optional[str]:
    s = _to_str(value)
    if not s:
        return None
    key = s.lower().strip()
    return STATUS_MAP.get(key, key)


def clean_row(row: Dict[str, Any], entity: str) -> Dict[str, Any]:
    """
    Clean a mapped row (keys are already Eleva field names).
    """
    out: Dict[str, Any] = {}

    if entity == "customers":
        out["customer_id"] = _to_str(row.get("customer_id"))
        out["total_orders"] = _to_int(row.get("total_orders")) or 0
        out["total_spent"] = _to_float(row.get("total_spent")) or 0.0
        out["days_since_last_order"] = _to_int(row.get("days_since_last_order"))
        out["churn_risk_score"] = _to_float(row.get("churn_risk_score"))
        out["email"] = _to_str(row.get("email"))
        out["segment"] = _to_str(row.get("segment"))

    elif entity == "orders":
        out["order_id"] = _to_str(row.get("order_id"))
        out["customer_id"] = _to_str(row.get("customer_id"))
        out["status"] = _normalize_status(row.get("status")) or "unknown"
        out["total"] = _to_float(row.get("total")) or 0.0
        out["order_date"] = _parse_date(row.get("order_date"))

    elif entity == "campaigns":
        out["campaign_id"] = _to_str(row.get("campaign_id"))
        out["name"] = _to_str(row.get("name"))
        out["type"] = _to_str(row.get("type"))
        out["conversion_rate"] = _to_float(row.get("conversion_rate"))
        out["roi"] = _to_float(row.get("roi"))

    return out
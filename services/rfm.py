"""
RFM Analysis – Recency, Frequency, Monetary.

Produces a segment for each customer:
Champions, Loyal, Potential Loyalists, At Risk, Hibernating, Lost, New.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_rfm(
    customers: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    reference_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Compute RFM scores and segments for each customer.
    Robust to None / missing fields (typical after CSV import).
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"orders": 0, "total": 0.0, "last_date": None}
    )

    for order in orders:
        if order.get("status") != "completed":
            continue
        cid = order.get("customer_id")
        if not cid:
            continue
        stats[cid]["orders"] += 1
        stats[cid]["total"] += _safe_float(order.get("total"))
        try:
            raw = str(order.get("order_date", "") or "")[:10]
            if raw:
                od = datetime.fromisoformat(raw)
                if stats[cid]["last_date"] is None or od > stats[cid]["last_date"]:
                    stats[cid]["last_date"] = od
        except Exception:
            pass

    raw_rows = []
    for c in customers:
        cid = c.get("customer_id")
        s = stats.get(cid, {"orders": 0, "total": 0.0, "last_date": None})

        if s["last_date"]:
            recency = (reference_date.replace(tzinfo=None) - s["last_date"]).days
            recency = max(recency, 0)
        else:
            # None-safe (key may exist with value null after import)
            recency = _safe_int(c.get("days_since_last_order"), 999)

        frequency = s["orders"] or _safe_int(c.get("total_orders"), 0)
        monetary = s["total"] or _safe_float(c.get("total_spent"), 0.0)

        raw_rows.append({
            "customer_id": cid,
            "recency_days": recency,
            "frequency": frequency,
            "monetary": round(monetary, 2),
        })

    if not raw_rows:
        return []

    def score_by_quintile(values: List[float], reverse: bool = False) -> List[int]:
        sorted_vals = sorted(set(values), reverse=reverse)
        if len(sorted_vals) == 1:
            return [3] * len(values)
        scores = []
        for v in values:
            rank = sorted_vals.index(v) if v in sorted_vals else 0
            q = int(rank / max(len(sorted_vals) - 1, 1) * 4) + 1
            scores.append(q)
        return scores

    recencies = [r["recency_days"] for r in raw_rows]
    frequencies = [r["frequency"] for r in raw_rows]
    monetaries = [r["monetary"] for r in raw_rows]

    r_scores = score_by_quintile(recencies, reverse=True)
    f_scores = score_by_quintile(frequencies, reverse=False)
    m_scores = score_by_quintile(monetaries, reverse=False)

    results = []
    for i, r in enumerate(raw_rows):
        rs, fs, ms = r_scores[i], f_scores[i], m_scores[i]
        segment = _rfm_segment(rs, fs, ms)
        results.append({
            **r,
            "r_score": rs,
            "f_score": fs,
            "m_score": ms,
            "rfm_segment": segment,
        })

    return results


def _rfm_segment(r: int, f: int, m: int) -> str:
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal"
    if r >= 4 and f <= 2:
        return "New / Promising"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2 and m >= 3:
        return "Hibernating (high value)"
    if r <= 2 and f <= 2:
        return "Lost / Churned"
    if r >= 3 and f <= 2:
        return "Potential Loyalist"
    return "Need Attention"
"""
RFM Analysis – Recency, Frequency, Monetary.

Produces a segment for each customer:
Champions, Loyal, Potential Loyalists, At Risk, Hibernating, Lost, New.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from collections import defaultdict


def compute_rfm(
    customers: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    reference_date: datetime | None = None,
) -> List[Dict[str, Any]]:
    """
    Compute RFM scores and segments for each customer.

    Returns a list of dicts:
    {
      customer_id, recency_days, frequency, monetary,
      r_score, f_score, m_score, rfm_segment
    }
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    # Aggregate orders per customer (completed only)
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
        stats[cid]["total"] += float(order.get("total", 0))
        try:
            od = datetime.fromisoformat(str(order.get("order_date", ""))[:10])
            if stats[cid]["last_date"] is None or od > stats[cid]["last_date"]:
                stats[cid]["last_date"] = od
        except Exception:
            pass

    # Build raw RFM values
    raw = []
    for c in customers:
        cid = c.get("customer_id")
        s = stats.get(cid, {"orders": 0, "total": 0.0, "last_date": None})

        if s["last_date"]:
            recency = (reference_date.replace(tzinfo=None) - s["last_date"]).days
        else:
            # Fallback: use days_since_last_order if present
            recency = int(c.get("days_since_last_order", 999))

        frequency = s["orders"] or int(c.get("total_orders", 0))
        monetary = s["total"] or float(c.get("total_spent", 0))

        raw.append({
            "customer_id": cid,
            "recency_days": max(recency, 0),
            "frequency": frequency,
            "monetary": round(monetary, 2),
        })

    if not raw:
        return []

    # Score 1-5 (5 = best)
    def score_by_quintile(values: List[float], reverse: bool = False) -> List[int]:
        """Simple 5-level scoring."""
        sorted_vals = sorted(set(values), reverse=reverse)
        if len(sorted_vals) == 1:
            return [3] * len(values)
        scores = []
        for v in values:
            # rank position
            rank = sorted_vals.index(v) if v in sorted_vals else 0
            # map to 1-5
            q = int(rank / max(len(sorted_vals) - 1, 1) * 4) + 1
            scores.append(q)
        return scores

    recencies = [r["recency_days"] for r in raw]
    frequencies = [r["frequency"] for r in raw]
    monetaries = [r["monetary"] for r in raw]

    # Recency: lower is better → reverse=True for scoring
    r_scores = score_by_quintile(recencies, reverse=True)
    f_scores = score_by_quintile(frequencies, reverse=False)
    m_scores = score_by_quintile(monetaries, reverse=False)

    results = []
    for i, r in enumerate(raw):
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
    """
    Map RFM scores to a readable segment.
    Simple rules (can be refined later).
    """
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
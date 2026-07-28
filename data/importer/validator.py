"""
Validate cleaned rows against Eleva requirements.
"""

from typing import Any, Dict, List, Tuple

from data.importer.schema import REQUIRED


def validate_row(row: Dict[str, Any], entity: str) -> Tuple[bool, str]:
    """
    Returns (is_valid, reason).
    """
    for field in REQUIRED.get(entity, []):
        val = row.get(field)
        if val is None or val == "":
            return False, f"missing required field '{field}'"

    if entity == "orders":
        if row.get("total") is not None and row["total"] < 0:
            return False, "negative total"

    if entity == "customers":
        if row.get("total_spent") is not None and row["total_spent"] < 0:
            return False, "negative total_spent"

    return True, ""


def validate_dataset(
    rows: List[Dict[str, Any]],
    entity: str,
    max_reject_ratio: float = 0.5,
) -> Dict[str, Any]:
    """
    Validate all rows. Return accepted, rejected, and stats.
    """
    accepted = []
    rejected = []

    for i, row in enumerate(rows):
        ok, reason = validate_row(row, entity)
        if ok:
            accepted.append(row)
        else:
            rejected.append({"row_index": i, "reason": reason, "data": row})

    total = len(rows) or 1
    reject_ratio = len(rejected) / total

    return {
        "accepted": accepted,
        "rejected": rejected,
        "total_read": len(rows),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "reject_ratio": round(reject_ratio, 3),
        "too_many_rejects": reject_ratio > max_reject_ratio,
    }
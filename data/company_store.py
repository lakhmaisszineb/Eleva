"""
CompanyStore – Access layer for private company data (SQLite-backed).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from config import settings, get_logger
from core.exceptions import DataNotFoundError, InvalidCompanyError
from core.models import CompanyContext
from data.db import get_connection, init_db, loads

logger = get_logger(__name__)

_CUSTOMER_CORE_FIELDS = [
    "customer_id", "total_orders", "total_spent",
    "days_since_last_order", "churn_risk_score", "email", "segment",
]
_ORDER_CORE_FIELDS = ["order_id", "customer_id", "status", "total", "order_date"]
_CAMPAIGN_CORE_FIELDS = ["campaign_id", "name", "type", "conversion_rate", "roi"]


def _row_to_dict(row, core_fields: List[str]) -> Dict[str, Any]:
    out = {field: row[field] for field in core_fields}
    out.update(loads(row["extra_json"]))
    return out


class CompanyStore:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        self.db_path = self.data_dir / "eleva.db"  
        init_db(self.db_path)
        logger.info(f"CompanyStore initialized with data_dir={self.data_dir} (SQLite)")

    def get_company_context(self, company_id: str) -> CompanyContext:
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT * FROM company_profile WHERE company_id = ?", (company_id,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            raise DataNotFoundError(f"Profile not found for company '{company_id}'")
        return CompanyContext(
            company_id=company_id,
            name=row["name"],
            industry=row["industry"],
            description=row["description"],
            goals=loads(row["goals_json"]) or [],
            current_focus=row["current_focus"],
            metadata=loads(row["metadata_json"]) or {},
        )

    def get_customers(self, company_id: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM customers WHERE company_id = ?", (company_id,)).fetchall()
        finally:
            conn.close()
        return [_row_to_dict(r, _CUSTOMER_CORE_FIELDS) for r in rows]

    def get_orders(self, company_id: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM orders WHERE company_id = ?", (company_id,)).fetchall()
        finally:
            conn.close()
        return [_row_to_dict(r, _ORDER_CORE_FIELDS) for r in rows]

    def get_campaigns(self, company_id: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute("SELECT * FROM campaigns WHERE company_id = ?", (company_id,)).fetchall()
        finally:
            conn.close()
        return [_row_to_dict(r, _CAMPAIGN_CORE_FIELDS) for r in rows]

    def list_available_companies(self) -> List[str]:
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute("SELECT company_id FROM company_profile").fetchall()
        finally:
            conn.close()
        return [r["company_id"] for r in rows]

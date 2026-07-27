"""
CompanyStore – Access layer for private company data.

Responsibilities:
- Load company data in a multi-tenant safe way (by company_id)
- Provide clean methods for the Observe step
- Keep the Decision Engine independent from the storage format

Current implementation: JSON files.
Future: PostgreSQL + pgvector.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import settings, get_logger
from core.exceptions import DataNotFoundError, InvalidCompanyError
from core.models import CompanyContext

logger = get_logger(__name__)


class CompanyStore:
    """
    Simple multi-tenant data access layer.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.data_dir
        logger.info(f"CompanyStore initialized with data_dir={self.data_dir}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _company_path(self, company_id: str) -> Path:
        path = self.data_dir / company_id
        if not path.exists():
            raise InvalidCompanyError(f"Company '{company_id}' not found in {self.data_dir}")
        return path

    def _load_json(self, company_id: str, filename: str) -> Any:
        file_path = self._company_path(company_id) / filename
        if not file_path.exists():
            raise DataNotFoundError(f"File '{filename}' not found for company '{company_id}'")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # Public API used by the Decision Engine
    # ------------------------------------------------------------------

    def get_company_context(self, company_id: str) -> CompanyContext:
        """Load the high-level company profile."""
        raw = self._load_json(company_id, "profile.json")
        return CompanyContext(
            company_id=company_id,
            name=raw["name"],
            industry=raw["industry"],
            description=raw.get("description"),
            goals=raw.get("goals", []),
            current_focus=raw.get("current_focus"),
            metadata=raw.get("metadata", {}),
        )

    def get_customers(self, company_id: str) -> List[Dict[str, Any]]:
        """Return all customers for a company."""
        return self._load_json(company_id, "customers.json")

    def get_orders(self, company_id: str) -> List[Dict[str, Any]]:
        """Return all orders for a company."""
        return self._load_json(company_id, "orders.json")

    def get_campaigns(self, company_id: str) -> List[Dict[str, Any]]:
        """Return all marketing campaigns for a company."""
        return self._load_json(company_id, "campaigns.json")

    def list_available_companies(self) -> List[str]:
        """Return list of company_ids that have data."""
        if not self.data_dir.exists():
            return []
        return [p.name for p in self.data_dir.iterdir() if p.is_dir()]
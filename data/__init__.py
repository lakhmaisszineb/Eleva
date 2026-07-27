"""
data package

Handles private company data (multi-tenant).
Never put marketing playbooks here — those belong to knowledge/.
"""

from data.company_store import CompanyStore

__all__ = ["CompanyStore"]
"""
Company administration helpers (create-only), for the Streamlit UI.

Kept strictly separate from CompanyStore (read layer used by the Decision
Engine) and from the engine/services themselves. Pure data management,
no business logic — creating a company is not a decision-engine concern.
"""

from typing import Any, Dict, List, Optional

from data.db import get_connection, init_db, upsert_profile


def company_exists(company_id: str) -> bool:
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM company_profile WHERE company_id = ?", (company_id,)
        ).fetchone()
    finally:
        conn.close()
    return row is not None


def create_company(
    company_id: str,
    name: str,
    industry: str,
    description: Optional[str] = None,
    goals: Optional[List[str]] = None,
    current_focus: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Create a new company profile.
    Raises ValueError if the company_id already exists (no silent overwrite).
    """
    company_id = (company_id or "").strip()
    if not company_id:
        raise ValueError("L'identifiant de l'entreprise ne peut pas être vide.")
    if company_exists(company_id):
        raise ValueError(f"L'entreprise « {company_id} » existe déjà.")

    profile = {
        "name": name,
        "industry": industry,
        "description": description,
        "current_focus": current_focus,
        "goals": goals or [],
        "metadata": metadata or {},
    }
    conn = get_connection()
    try:
        upsert_profile(conn, company_id, profile)
        conn.commit()
    finally:
        conn.close()

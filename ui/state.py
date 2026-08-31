"""
Session state helpers and cached backend accessors for the Streamlit UI.

Nothing here touches business logic: it only wires the existing
CompanyStore / DecisionEngine / KnowledgeBase / services to Streamlit's
session and caching primitives.
"""

from typing import Optional

import streamlit as st

from data.company_store import CompanyStore
from engine.decision_engine import DecisionEngine


@st.cache_resource(show_spinner=False)
def get_engine() -> DecisionEngine:
    return DecisionEngine()


def get_store() -> CompanyStore:
    # Cheap to instantiate (opens/closes a SQLite connection per call);
    # not cached so newly imported/created data is always visible.
    return CompanyStore()


def init_session_state() -> None:
    defaults = {
        "company_id": None,
        "decision_state": None,   # last DecisionState (pydantic object)
        "explanation": None,      # last explanation dict
        "last_import_report": None,
        "nav": "Tableau de bord",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def available_companies():
    try:
        return sorted(get_store().list_available_companies())
    except Exception:
        return []


def current_company_id() -> Optional[str]:
    return st.session_state.get("company_id")


def set_current_company(company_id: str) -> None:
    if st.session_state.get("company_id") != company_id:
        # Switching company invalidates any previous analysis shown on screen.
        st.session_state["decision_state"] = None
        st.session_state["explanation"] = None
        st.session_state["last_import_report"] = None
    st.session_state["company_id"] = company_id

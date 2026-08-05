"""Composants UI Eleva."""

import streamlit as st
from typing import Any, Dict, List

from ui.theme import KPI_LABELS_FR


def inject_css(css: str):
    st.markdown(css, unsafe_allow_html=True)


def topbar(api_ok: bool):
    status = (
        '<span class="status-dot"><span class="dot dot-on"></span> Agent disponible</span>'
        if api_ok
        else '<span class="status-dot"><span class="dot dot-off"></span> Agent hors ligne</span>'
    )
    st.markdown(
        f"""
        <div class="topbar">
            <div class="brand">
                <span class="name">Eleva</span>
                <span class="sub">Agent de décision marketing · Solution IT</span>
            </div>
            {status}
        </div>
        """,
        unsafe_allow_html=True,
    )


def navbar(pages: List[str]) -> str:
    current = st.session_state.get("page", pages[0])
    cols = st.columns(len(pages))
    for i, p in enumerate(pages):
        with cols[i]:
            if st.button(
                p,
                key=f"nav_{p}",
                use_container_width=True,
                type="primary" if p == current else "secondary",
            ):
                st.session_state.page = p
                st.rerun()
    return st.session_state.get("page", pages[0])


def section_title(text: str):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def kpi_card(name: str, value: Any, unit: str = ""):
    label = KPI_LABELS_FR.get(name, name.replace("_", " ").capitalize())
    display = value
    suffix = ""
    if unit == "ratio" and isinstance(value, (int, float)):
        display = f"{float(value):.0%}"
    elif unit == "currency" and isinstance(value, (int, float)):
        display = f"{float(value):,.2f}"
        suffix = " €"
    elif unit and unit not in ("ratio", "currency"):
        suffix = f" {unit}"
    st.markdown(
        f"""
        <div class="eleva-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{display}{suffix}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_priority(priority: str) -> str:
    p = (priority or "medium").lower()
    labels = {
        "high": "ÉLEVÉE",
        "medium": "MOYENNE",
        "low": "FAIBLE",
        "critical": "CRITIQUE",
    }
    return f'<span class="badge badge-{p}">{labels.get(p, p.upper())}</span>'


def badge_type(t: str) -> str:
    t = (t or "problem").lower()
    label = "Problème" if t == "problem" else "Opportunité"
    return f'<span class="badge badge-{t}">{label}</span>'


def issue_card(issue: Dict[str, Any]):
    st.markdown(
        f"""
        <div class="eleva-card">
            {badge_priority(issue.get("priority", ""))}
            {badge_type(issue.get("type", ""))}
            <h4 style="margin:0.5rem 0 0.35rem 0;">{issue.get("title", "")}</h4>
            <p style="color:#64748B;margin:0;font-size:0.92rem;">{issue.get("description", "")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def reco_card(reco: Dict[str, Any]):
    p = (reco.get("priority") or "medium").lower()
    st.markdown(
        f"""
        <div class="reco-card {p}">
            {badge_priority(p)}
            <h4 style="margin:0.45rem 0;">{reco.get("title", "")}</h4>
            <p style="color:#334155;margin:0 0 0.5rem 0;">{reco.get("summary", "")}</p>
            <p style="font-size:0.88rem;color:#64748B;margin:0;">
                <strong>Justification :</strong> {reco.get("justification", "")}
            </p>
            <p style="font-size:0.78rem;color:#94A3B8;margin:0.5rem 0 0 0;">
                Statut : en attente d'approbation
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
"""
Reusable presentation components for the Eleva Streamlit interface.

These functions only render markup — they never call business logic
themselves. Views are responsible for fetching data and passing it in.
"""

from typing import Any, Dict, List, Optional

import streamlit as st

from ui.theme import COLORS, PRIORITY_COLOR, ISSUE_TYPE_COLOR


PRIORITY_LABEL_FR = {
    "low": "Faible",
    "medium": "Moyenne",
    "high": "Élevée",
    "critical": "Critique",
}

ISSUE_TYPE_LABEL_FR = {
    "problem": "Problème",
    "opportunity": "Opportunité",
}

STEP_LABELS_FR = [
    "Comprendre", "Observer", "Détecter", "Rechercher",
    "Raisonner", "Planifier", "Décider", "Recommander",
]


def section_title(text: str) -> None:
    st.markdown(f'<div class="eleva-section-title">{text}</div>', unsafe_allow_html=True)


def caption(text: str) -> None:
    st.markdown(f'<p class="eleva-caption">{text}</p>', unsafe_allow_html=True)


def priority_badge(priority: str) -> str:
    priority = (priority or "medium").lower()
    color, bg = PRIORITY_COLOR.get(priority, PRIORITY_COLOR["medium"])
    label = PRIORITY_LABEL_FR.get(priority, priority.capitalize())
    return (
        f'<span class="eleva-badge" style="color:{color};background-color:{bg};">'
        f"Priorité {label}</span>"
    )


def issue_type_badge(issue_type: str) -> str:
    issue_type = (issue_type or "problem").lower()
    color, bg = ISSUE_TYPE_COLOR.get(issue_type, ISSUE_TYPE_COLOR["problem"])
    label = ISSUE_TYPE_LABEL_FR.get(issue_type, issue_type.capitalize())
    return f'<span class="eleva-badge" style="color:{color};background-color:{bg};">{label}</span>'


def status_badge(status: str) -> str:
    labels = {
        "draft": ("Brouillon", COLORS["gray"], COLORS["gray_light"]),
        "pending_approval": ("En attente de validation", COLORS["amber"], COLORS["amber_light"]),
        "approved": ("Approuvée", COLORS["sage"], COLORS["sage_light"]),
        "rejected": ("Rejetée", COLORS["brick"], COLORS["brick_light"]),
    }
    label, color, bg = labels.get(status, (status, COLORS["gray"], COLORS["gray_light"]))
    return f'<span class="eleva-badge" style="color:{color};background-color:{bg};">{label}</span>'


def kpi_card(label: str, value: Any, unit: Optional[str] = None) -> None:
    display = value
    if isinstance(value, float):
        display = f"{value:,.2f}".replace(",", " ")
    unit_suffix = ""
    if unit == "ratio":
        try:
            display = f"{float(value):.0%}"
        except (TypeError, ValueError):
            pass
    elif unit == "currency":
        try:
            display = f"{float(value):,.2f} €".replace(",", " ")
        except (TypeError, ValueError):
            pass
    st.markdown(
        f"""
        <div class="eleva-kpi">
            <div class="eleva-kpi-label">{label}</div>
            <div class="eleva-kpi-value">{display}{unit_suffix}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_grid(kpis: List[Dict[str, Any]], labels_fr: Dict[str, str], per_row: int = 4) -> None:
    """kpis: list of {"name", "value", "unit"} dicts (as produced by the Observe step)."""
    if not kpis:
        empty_state("Aucun indicateur disponible pour le moment.")
        return
    rows = [kpis[i:i + per_row] for i in range(0, len(kpis), per_row)]
    for row in rows:
        cols = st.columns(len(row))
        for col, kpi in zip(cols, row):
            with col:
                label = labels_fr.get(kpi["name"], kpi["name"].replace("_", " ").capitalize())
                kpi_card(label, kpi["value"], kpi.get("unit"))


def empty_state(message: str) -> None:
    st.markdown(f'<div class="eleva-empty">{message}</div>', unsafe_allow_html=True)


def error_banner(title: str, detail: str, hint: str = "") -> None:
    st.error(f"**{title}**\n\n{detail}" + (f"\n\n**À faire :** {hint}" if hint else ""))


def pipeline_stepper(current_step: Optional[str] = None, completed: bool = False) -> None:
    """Visual, non-technical representation of the 8-step Decision Engine cycle."""
    step_keys = [
        "understand", "observe", "detect", "retrieve",
        "reason", "plan", "decide", "recommend",
    ]
    html_parts = ['<div class="eleva-stepper">']
    for i, (key, label) in enumerate(zip(step_keys, STEP_LABELS_FR)):
        is_done = completed or (current_step and step_keys.index(current_step) > i if current_step in step_keys else False)
        style = "opacity:1;" if (completed or is_done) else "opacity:0.45;"
        html_parts.append(f'<span class="eleva-step" style="{style}">{i+1}. {label}</span>')
        if i < len(step_keys) - 1:
            html_parts.append('<span class="eleva-step-arrow">→</span>')
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def quote_block(text: str) -> None:
    st.markdown(f'<div class="eleva-quote">{text}</div>', unsafe_allow_html=True)

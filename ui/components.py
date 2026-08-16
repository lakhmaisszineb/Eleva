"""
Composants UI Eleva réutilisables.
"""

import streamlit as st
from ui.theme import PRIMARY, TEXT_MUTED, BORDER, PRIORITY_MAP, ISSUE_TYPE_MAP, KPI_LABELS_FR, SUCCESS


def inject_css(css: str):
    """Injecte du CSS personnalisé dans la page."""
    st.markdown(css, unsafe_allow_html=True)


def top_nav(is_online: bool = True):
    """Barre de navigation supérieure avec logo et statut."""
    status_class = "dot-online" if is_online else "dot-offline"
    status_text = "Connecté" if is_online else "Hors ligne"

    st.markdown(f"""
    <div class="nav-bar">
        <div class="logo-text">
            <span>◈</span> Eleva
        </div>
        <div class="status-indicator">
            <div class="dot {status_class}"></div>
            {status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None):
    """En-tête de page avec titre et sous-titre."""
    st.markdown(f'<div class="h1">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: any, unit: str = "", help_text: str = None):
    """Carte KPI stylisée."""
    # Traduction automatique si possible
    display_label = KPI_LABELS_FR.get(label, label)

    # Formatage de la valeur
    if isinstance(value, float):
        if "rate" in label or "ratio" in label or unit == "%":
            formatted_value = f"{value*100:.1f}" if value < 1 else f"{value:.1f}"
            unit = "%"
        else:
            formatted_value = f"{value:,.2f}".replace(",", " ")
    else:
        formatted_value = str(value)

    st.markdown(f"""
    <div class="card kpi-card">
        <div class="kpi-label">{display_label}</div>
        <div class="kpi-value">
            {formatted_value}<span class="kpi-unit">{unit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, style: str = "badge-slate"):
    """Badge générique."""
    return f'<span class="badge {style}">{text}</span>'


def issue_card(issue: dict):
    """Carte pour afficher un problème ou une opportunité détectée."""
    i_type = issue.get("type", "problem")
    type_info = ISSUE_TYPE_MAP.get(i_type, ISSUE_TYPE_MAP["problem"])
    priority = issue.get("priority", "medium").lower()
    p_info = PRIORITY_MAP.get(priority, PRIORITY_MAP["medium"])

    evidence_html = ""
    if issue.get("evidence"):
        evidence_list = "".join([f"<li>{e}</li>" for e in issue["evidence"][:3]])
        evidence_html = f"""
        <div style="margin-top: 0.75rem; font-size: 0.85rem;">
            <strong style="color: {TEXT_MUTED};">Preuves :</strong>
            <ul style="margin-top: 0.25rem; padding-left: 1.25rem; color: {TEXT_MUTED};">
                {evidence_list}
            </ul>
        </div>
        """

    st.markdown(f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div style="font-weight: 700; font-size: 1.1rem;">{type_info['icon']} {issue.get('title')}</div>
            {badge(p_info['label'], p_info['class'])}
        </div>
        <div style="font-size: 0.9rem; color: {TEXT_MUTED}; line-height: 1.4;">
            {issue.get('description')}
        </div>
        {evidence_html}
    </div>
    """, unsafe_allow_html=True)


def recommendation_card(reco: dict):
    """Carte détaillée pour une recommandation stratégique."""
    priority = reco.get("priority", "medium").lower()
    p_info = PRIORITY_MAP.get(priority, PRIORITY_MAP["medium"])
    reco_class = f"reco-{priority}"

    st.markdown(f"""
    <div class="card reco-card {reco_class}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div style="font-weight: 700; font-size: 1.25rem; color: {PRIMARY};">{reco.get('title')}</div>
            {badge(p_info['label'], p_info['class'])}
        </div>
        <div style="margin-bottom: 1rem; font-size: 1rem; font-weight: 500;">
            {reco.get('summary')}
        </div>
        <div style="background-color: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid {BORDER};">
            <div style="font-size: 0.75rem; font-weight: 700; color: {TEXT_MUTED}; text-transform: uppercase; margin-bottom: 0.5rem;">Justification stratégique</div>
            <div style="font-size: 0.9rem; line-height: 1.5;">{reco.get('justification')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Voir le plan d'action détaillé"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Prochaines étapes :**")
            for step in reco.get("next_steps", []):
                st.markdown(f"- {step}")
        with col2:
            st.markdown("**Résultats attendus :**")
            for outcome in reco.get("expected_outcomes", []):
                st.markdown(f"- {outcome}")


def analysis_step(title: str, description: str, is_active: bool = False, is_completed: bool = False):
    """Composant pour afficher une étape du Decision Engine."""
    active_class = "step-active" if is_active else ""
    dot_style = f"background-color: {SUCCESS}; border-color: {SUCCESS};" if is_completed else ""

    st.markdown(f"""
    <div class="step-item {active_class}">
        <div class="step-dot" style="{dot_style}"></div>
        <div class="step-title">{title}</div>
        <div class="step-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def empty_state(title: str, message: str, icon: str = "🔍"):
    """État vide pour les pages sans données."""
    st.markdown(f"""
    <div style="text-align: center; padding: 4rem 2rem; background-color: white; border-radius: 12px; border: 1px dashed {BORDER};">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{icon}</div>
        <div style="font-size: 1.25rem; font-weight: 700; margin-bottom: 0.5rem;">{title}</div>
        <div style="color: {TEXT_MUTED}; max-width: 400px; margin: 0 auto;">{message}</div>
    </div>
    """, unsafe_allow_html=True)


def playbook_card(playbook: dict):
    """Affiche un guide marketing (playbook) de manière élégante."""
    st.markdown(f"""
    <div class="card" style="border-top: 4px solid {SUCCESS};">
        <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem; color: {SUCCESS};">
            📖 {playbook.get('Technique', 'Guide Stratégique')}
        </div>
        <div style="font-size: 0.9rem; margin-bottom: 0.75rem;">
            <strong>Objectif :</strong> {playbook.get('Goal', 'Non spécifié')}
        </div>
        <div style="font-size: 0.85rem; color: {TEXT_MUTED}; margin-bottom: 0.75rem;">
            <strong>Quand l'utiliser :</strong> {playbook.get('When to use', 'N/A')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Voir les actions recommandées"):
        actions = playbook.get('Recommended Actions', [])
        if isinstance(actions, list):
            for action in actions:
                st.markdown(f"- {action}")
        else:
            st.write(actions)

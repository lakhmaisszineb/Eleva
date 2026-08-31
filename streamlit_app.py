"""
Eleva — Interface Streamlit.

Lancer depuis la racine du projet (venv activé) :
    streamlit run streamlit_app.py
"""

import streamlit as st
from streamlit_option_menu import option_menu

from ui.theme import configure_page
from ui.state import (
    init_session_state, available_companies, current_company_id, set_current_company,
)
from ui.views import (
    view_dashboard, view_data, view_analysis, view_clients, view_about,
    render_company_creation_form,
)

configure_page("Eleva")
init_session_state()

NAV_ITEMS = ["Tableau de bord", "Données", "Analyse", "Clients", "Comment ça marche"]
NAV_ICONS = ["speedometer2", "database", "graph-up-arrow", "people", "question-circle"]


# ---------------------------------------------------------------------------
# Sidebar : identity, company selection, navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        f"<h2 style='color:{'#1F2A44'};margin-bottom:0;'>Eleva</h2>"
        f"<p style='color:{'#6B6F76'};margin-top:0.1rem;font-size:0.85rem;'>"
        "Agent de décision marketing</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    companies = available_companies()

    if companies:
        default_id = current_company_id() or companies[0]
        if default_id not in companies:
            default_id = companies[0]
        selected = st.selectbox(
            "Entreprise",
            options=companies,
            index=companies.index(default_id),
        )
        set_current_company(selected)
    else:
        st.info("Aucune entreprise enregistrée pour le moment. Créez-en une ci-dessous.")

    with st.expander("Ajouter une entreprise", expanded=not companies):
        render_company_creation_form()

    st.markdown("---")

    nav_choice = option_menu(
        menu_title=None,
        options=NAV_ITEMS,
        icons=NAV_ICONS,
        default_index=NAV_ITEMS.index(st.session_state.get("nav", "Tableau de bord")),
        styles={
            "container": {"padding": "0", "background-color": "transparent"},
            "icon": {"color": "#1F2A44", "font-size": "15px"},
            "nav-link": {
                "font-size": "14.5px", "color": "#1F2A44", "text-align": "left",
                "margin": "2px 0", "border-radius": "8px",
            },
            "nav-link-selected": {"background-color": "#B5793B", "color": "#FFFFFF"},
        },
    )
    st.session_state["nav"] = nav_choice

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

company_id = current_company_id()

if nav_choice == "Comment ça marche":
    view_about()
elif not company_id:
    st.markdown("## Bienvenue sur Eleva")
    st.markdown(
        "Créez ou sélectionnez une entreprise dans le menu latéral pour commencer : "
        "consulter ses données, lancer une analyse ou explorer les recommandations client."
    )
else:
    if nav_choice == "Tableau de bord":
        view_dashboard(company_id)
    elif nav_choice == "Données":
        view_data(company_id)
    elif nav_choice == "Analyse":
        view_analysis(company_id)
    elif nav_choice == "Clients":
        view_clients(company_id)

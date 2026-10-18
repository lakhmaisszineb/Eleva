"""
Page-level views for the Eleva Streamlit interface.

Each function renders one section of the app. Views call existing
project modules directly (CompanyStore, DecisionEngine, importer,
services) and never re-implement business logic.
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

from core.models import AnalysisRequest
from core.exceptions import ElevaError
from data.company_admin import create_company, company_exists
from data.importer.csv_importer import import_csv
from services.client_recommendations import (
    recommend_for_customers,
    build_strategic_notes_from_analysis,
)
from ui.components import (
    section_title, caption, empty_state, error_banner, pipeline_stepper,
)
from ui.errors import humanize_error
from ui.pipeline_view import render_decision_state, render_explanation
from ui.state import get_store, get_engine, current_company_id

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"

ENTITY_LABELS_FR = {
    "customers": "Clients",
    "orders": "Commandes",
    "campaigns": "Campagnes",
}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def view_dashboard(company_id: str) -> None:
    store = get_store()

    try:
        ctx = store.get_company_context(company_id)
    except Exception as exc:
        title, detail, hint = humanize_error(exc)
        error_banner(title, detail, hint)
        return

    st.markdown(f"## {ctx.name}")
    cols = st.columns([2, 1])
    with cols[0]:
        if ctx.description:
            st.markdown(ctx.description)
        st.markdown(f"**Secteur :** {ctx.industry}")
        if ctx.current_focus:
            st.markdown(f"**Objectif prioritaire actuel :** {ctx.current_focus}")
        if ctx.goals:
            section_title("Objectifs de l'entreprise")
            for g in ctx.goals:
                st.markdown(f"- {g}")
    with cols[1]:
        customers = store.get_customers(company_id)
        orders = store.get_orders(company_id)
        campaigns = store.get_campaigns(company_id)
        st.markdown(
            f"""
            <div class="eleva-card">
                <div class="eleva-kpi-label">Volume de données disponible</div>
                <p style="margin:0.4rem 0;">Clients : <strong>{len(customers)}</strong></p>
                <p style="margin:0.4rem 0;">Commandes : <strong>{len(orders)}</strong></p>
                <p style="margin:0.4rem 0;">Campagnes : <strong>{len(campaigns)}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    section_title("Comment fonctionne Eleva")
    caption(
        "Chaque analyse suit un cycle de décision en 8 étapes, du recueil des données "
        "jusqu'à la recommandation finale, toujours soumise à validation humaine."
    )
    pipeline_stepper(completed=False)

    last_state = st.session_state.get("decision_state")
    if last_state and last_state.request.company_id == company_id:
        section_title("Dernière analyse réalisée pour cette entreprise")
        render_decision_state(last_state)
    else:
        empty_state(
            "Aucune analyse n'a encore été lancée pour cette entreprise. "
            "Rendez-vous dans l'onglet « Analyse » pour interroger l'agent de décision."
        )


# ---------------------------------------------------------------------------
# Data management
# ---------------------------------------------------------------------------

def view_data(company_id: str) -> None:
    store = get_store()

    section_title("Importer un nouveau fichier de données")
    caption(
        "Formats acceptés : fichiers CSV. Eleva identifie automatiquement les colonnes "
        "grâce à l'assistant IA (ou, à défaut, à une correspondance de secours), "
        "nettoie les données puis les enregistre pour cette entreprise."
    )

    entity = st.radio(
        "Type de données à importer",
        options=["customers", "orders", "campaigns"],
        format_func=lambda e: ENTITY_LABELS_FR[e],
        horizontal=True,
        key="import_entity",
    )
    uploaded = st.file_uploader("Déposer un fichier CSV", type=["csv"], key="import_file")

    if uploaded is not None and st.button("Lancer l'import", type="primary"):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        dest = UPLOAD_DIR / uploaded.name
        with open(dest, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Analyse et import du fichier en cours..."):
            try:
                result = import_csv(dest, entity=entity, company_id=company_id, write=True)
                st.session_state["last_import_report"] = result["report"]
                st.success(
                    f"Import réussi : {result['report']['accepted_count']} ligne(s) "
                    f"enregistrée(s) sur {result['report']['total_read']} lue(s)."
                )
            except Exception as exc:
                title, detail, hint = humanize_error(exc)
                error_banner(title, detail, hint)

    report = st.session_state.get("last_import_report")
    if report:
        with st.expander("Détail du dernier import", expanded=False):
            st.markdown(f"**Fichier :** `{Path(report['source_file']).name}`")
            st.markdown(
                f"**Correspondance des colonnes :** "
                f"{'assistée par IA' if report['mapping_source'] == 'llm' else 'automatique (règles de secours)'}"
            )
            st.markdown(f"**Lignes lues :** {report['total_read']}")
            st.markdown(f"**Lignes acceptées :** {report['accepted_count']}")
            st.markdown(f"**Lignes rejetées :** {report['rejected_count']} ({report['reject_ratio']:.0%})")
            if report["ignored_columns"]:
                st.markdown(f"**Colonnes ignorées :** {', '.join(report['ignored_columns'])}")
            if report["sample_reject_reasons"]:
                st.markdown("**Exemples de motifs de rejet :**")
                for reason in report["sample_reject_reasons"]:
                    st.markdown(f"- {reason}")

    section_title("Données actuellement disponibles")
    tabs = st.tabs([ENTITY_LABELS_FR[e] for e in ["customers", "orders", "campaigns"]])
    fetchers = {
        "customers": store.get_customers,
        "orders": store.get_orders,
        "campaigns": store.get_campaigns,
    }
    for tab, entity_key in zip(tabs, ["customers", "orders", "campaigns"]):
        with tab:
            try:
                rows = fetchers[entity_key](company_id)
            except Exception as exc:
                title, detail, hint = humanize_error(exc)
                error_banner(title, detail, hint)
                continue
            if not rows:
                empty_state(f"Aucune donnée « {ENTITY_LABELS_FR[entity_key]} » importée pour le moment.")
                continue
            st.caption(f"{len(rows)} ligne(s)")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=380)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def view_analysis(company_id: str) -> None:
    store = get_store()
    try:
        store.get_company_context(company_id)
    except Exception as exc:
        title, detail, hint = humanize_error(exc)
        error_banner(title, detail, hint)
        return

    section_title("Lancer une nouvelle analyse")
    caption(
        "Décrivez ce que vous souhaitez qu'Eleva analyse. L'agent va comprendre le contexte "
        "de l'entreprise, observer les données, détecter les problèmes et opportunités, "
        "consulter sa base de bonnes pratiques marketing, puis proposer des recommandations."
    )

    with st.form("analysis_form"):
        question = st.text_area(
            "Question ou objectif d'analyse",
            value="Analyse la situation actuelle et propose les actions prioritaires.",
            height=90,
        )
        focus_options = [
            "cart_abandonment", "churn", "loyalty", "campaigns", "new_customers",
        ]
        focus_labels = {
            "cart_abandonment": "Abandon de panier",
            "churn": "Perte de clients (churn)",
            "loyalty": "Fidélisation",
            "campaigns": "Performance des campagnes",
            "new_customers": "Nouveaux clients",
        }
        focus_areas = st.multiselect(
            "Domaines à approfondir (optionnel)",
            options=focus_options,
            format_func=lambda x: focus_labels[x],
        )
        max_recommendations = st.slider(
            "Nombre maximum de recommandations souhaitées", min_value=1, max_value=10, value=3,
        )
        submitted = st.form_submit_button("Lancer l'analyse", type="primary")

    if submitted:
        request = AnalysisRequest(
            company_id=company_id,
            question=question,
            focus_areas=focus_areas or None,
            max_recommendations=max_recommendations,
        )
        with st.spinner("Eleva analyse la situation de l'entreprise..."):
            try:
                state = get_engine().run(request)
            except Exception as exc:
                title, detail, hint = humanize_error(exc)
                error_banner(title, detail, hint)
                return

        if state.errors and not state.recommendations:
            title, detail, hint = humanize_error(ElevaError(state.errors[0]))
            error_banner(title, detail, hint)
            return

        st.session_state["decision_state"] = state
        st.session_state["explanation"] = None
        st.success("Analyse terminée.")

    state = st.session_state.get("decision_state")
    if state and state.request.company_id == company_id:
        section_title("Résultats de l'analyse")
        render_decision_state(state)
    elif not submitted:
        empty_state("Renseignez votre question ci-dessus puis lancez l'analyse.")


# ---------------------------------------------------------------------------
# Per-client recommendations
# ---------------------------------------------------------------------------

def view_clients(company_id: str) -> None:
    store = get_store()
    try:
        customers = store.get_customers(company_id)
        orders = store.get_orders(company_id)
    except Exception as exc:
        title, detail, hint = humanize_error(exc)
        error_banner(title, detail, hint)
        return

    if not customers:
        empty_state(
            "Aucun client importé pour cette entreprise. "
            "Rendez-vous dans l'onglet « Données » pour importer un fichier clients."
        )
        return

    section_title("Recommandations individuelles par client")
    caption(
        "Chaque client est positionné sur la segmentation RFM (Récence, Fréquence, Montant) "
        "puis associé à une action recommandée selon des règles métier explicables. "
        "Aucun appel au modèle de langage n'est effectué à ce niveau."
    )

    strategic_notes: Dict[str, str] = {}
    last_state = st.session_state.get("decision_state")
    if last_state and last_state.request.company_id == company_id:
        analysis_like = {
            "recommendations": [
                {"title": r.title, "summary": r.summary, "justification": r.justification}
                for r in last_state.recommendations
            ]
        }
        strategic_notes = build_strategic_notes_from_analysis(analysis_like)

    with st.spinner("Calcul des recommandations par client..."):
        results = recommend_for_customers(customers, orders, strategic_notes)

    df = pd.DataFrame(results)

    col1, col2 = st.columns(2)
    with col1:
        segments = sorted(df["segment"].dropna().unique().tolist())
        selected_segments = st.multiselect("Filtrer par segment RFM", options=segments)
    with col2:
        priorities = ["Élevée", "Moyenne", "Faible"]
        selected_priorities = st.multiselect("Filtrer par priorité", options=priorities)

    filtered = df
    if selected_segments:
        filtered = filtered[filtered["segment"].isin(selected_segments)]
    if selected_priorities:
        filtered = filtered[filtered["priorite"].isin(selected_priorities)]

    st.caption(f"{len(filtered)} client(s) affiché(s) sur {len(df)}")
    st.dataframe(
        filtered.rename(columns={
            "customer_id": "Client",
            "segment": "Segment RFM",
            "r_score": "Score R",
            "f_score": "Score F",
            "m_score": "Score M",
            "recency_days": "Récence (jours)",
            "frequency": "Fréquence",
            "monetary": "Montant total",
            "priorite": "Priorité",
            "action": "Action recommandée",
            "playbook": "Bonne pratique",
            "raison": "Raison",
        }),
        use_container_width=True,
        height=480,
    )


# ---------------------------------------------------------------------------
# Company creation (used by the sidebar)
# ---------------------------------------------------------------------------

def render_company_creation_form() -> None:
    with st.form("create_company_form", clear_on_submit=True):
        st.markdown("**Nouvelle entreprise**")
        new_id = st.text_input("Identifiant (ex : company_010)")
        new_name = st.text_input("Nom de l'entreprise")
        new_industry = st.text_input("Secteur d'activité")
        new_description = st.text_area("Description (optionnel)", height=70)
        new_focus = st.text_input("Objectif prioritaire actuel (optionnel)")
        submitted = st.form_submit_button("Créer l'entreprise")

    if submitted:
        if not new_id or not new_name or not new_industry:
            st.warning("L'identifiant, le nom et le secteur sont obligatoires.")
            return
        try:
            create_company(
                company_id=new_id.strip(),
                name=new_name.strip(),
                industry=new_industry.strip(),
                description=new_description.strip() or None,
                current_focus=new_focus.strip() or None,
            )
            st.success(f"Entreprise « {new_name} » créée.")
            st.session_state["company_id"] = new_id.strip()
            st.rerun()
        except Exception as exc:
            title, detail, hint = humanize_error(exc)
            error_banner(title, detail, hint)


# ---------------------------------------------------------------------------
# About / how it works
# ---------------------------------------------------------------------------

def view_about() -> None:
    section_title("Comment fonctionne Eleva")
    st.markdown(
        "Eleva est un agent de décision marketing. Il ne se contente pas d'afficher des "
        "statistiques : il observe les données de l'entreprise, identifie des problèmes et "
        "des opportunités, s'appuie sur une base de bonnes pratiques marketing, puis propose "
        "des recommandations argumentées — toujours soumises à validation humaine avant toute action."
    )

    steps_explained = [
        ("Comprendre", "Eleva charge le profil de l'entreprise : secteur, objectifs, priorités actuelles."),
        ("Observer", "Les données clients, commandes et campagnes sont analysées : indicateurs clés (KPIs) et segmentation RFM (Récence, Fréquence, Montant)."),
        ("Détecter", "À partir de ces observations, Eleva identifie des problèmes (ex. abandon de panier élevé) et des opportunités (ex. clients à forte valeur à activer)."),
        ("Rechercher", "Pour chaque problème ou opportunité, Eleva consulte sa base de bonnes pratiques marketing et retient les techniques les plus pertinentes."),
        ("Raisonner", "L'agent formule des hypothèses sur les causes et les leviers d'action possibles."),
        ("Planifier", "Ces hypothèses sont transformées en stratégies concrètes, avec leur impact attendu et leur effort estimé."),
        ("Décider", "Les stratégies sont priorisées selon la criticité des problèmes ou opportunités concernés."),
        ("Recommander", "Eleva formule des recommandations finales, justifiées, avec des prochaines étapes claires. Aucune action n'est exécutée automatiquement."),
    ]
    for i, (label, text) in enumerate(steps_explained, start=1):
        st.markdown(f"**{i}. {label}** — {text}")

    section_title("Recommandations individuelles par client")
    st.markdown(
        "En complément de l'analyse stratégique, Eleva propose une recommandation pour chaque "
        "client, fondée sur son positionnement RFM et des règles métier explicables — sans appel "
        "au modèle de langage à ce niveau, pour rester rapide et prévisible sur de gros volumes."
    )

    section_title("Transparence et données")
    st.markdown(
        "Chaque recommandation peut être expliquée : Eleva indique les signaux observés, "
        "les problèmes détectés et les bonnes pratiques mobilisées qui ont conduit à sa "
        "conclusion. Les données clients restent sous le contrôle de l'entreprise."
    )

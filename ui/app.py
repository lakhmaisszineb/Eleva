"""
Eleva — interface Streamlit professionnelle en français.

Lancement depuis la racine du projet :
    streamlit run ui/app.py
"""

from __future__ import annotations

import csv
import html
import json
import os
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# Permet d'importer les modules du projet lorsque Streamlit exécute ce fichier.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import requests
import streamlit as st

from config import settings
from data.catalog import list_companies
from data.importer import import_csv
from knowledge.loader import load_playbooks
from ui.components import (
    badge,
    empty_state,
    inject_css,
    issue_card,
    kpi_card,
    page_header,
    playbook_card,
    recommendation_card,
    top_nav,
)
from ui.theme import CUSTOM_CSS, KPI_LABELS_FR, PRIMARY, TEXT_MUTED


API_BASE = os.getenv("ELEVA_API_URL", "http://127.0.0.1:8000")

PAGES = [
    "Vue d’ensemble",
    "Importer",
    "Analyser",
    "Résultats",
    "Clients",
    "Statistiques",
    "Guides marketing",
    "Explication",
]

ANALYSIS_CHOICES = {
    "Vue d’ensemble — problèmes et actions prioritaires": (
        "Analyse la situation actuelle et propose les actions prioritaires."
    ),
    "Paniers abandonnés — récupération de ventes": (
        "Analyse surtout les paniers abandonnés et propose des actions de récupération prioritaires."
    ),
    "Churn et rétention — clients à risque": (
        "Analyse le risque de churn et la rétention, puis propose des actions prioritaires."
    ),
    "Fidélisation et taux de réachat": (
        "Analyse le taux de réachat et propose des actions de fidélisation prioritaires."
    ),
    "Nouveaux clients — conversion vers le 2e achat": (
        "Analyse les nouveaux clients et propose comment les convertir en clients récurrents."
    ),
    "Campagnes marketing — performance et ROI": (
        "Analyse la performance des campagnes marketing et propose des actions pour améliorer le ROI."
    ),
}


st.set_page_config(
    page_title="Eleva · Agent de décision",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css(CUSTOM_CSS)

if "page" not in st.session_state:
    st.session_state.page = "Vue d’ensemble"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "history" not in st.session_state:
    st.session_state.history = []


def api_healthy() -> bool:
    """Vérifie uniquement la disponibilité de l'API FastAPI."""
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).status_code == 200
    except Exception:
        return False


def call_analyze(company_id: str, question: str, max_rec: int = 3) -> Dict[str, Any]:
    """Appelle le contrat réel POST /analyze."""
    response = requests.post(
        f"{API_BASE}/analyze",
        json={
            "company_id": company_id,
            "question": question,
            "max_recommendations": max_rec,
        },
        timeout=120,
    )
    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"API {response.status_code}: {detail}")
    return response.json()


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def company_meta(company_id: str, companies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return next((item for item in companies if item.get("company_id") == company_id), None)


def normalize_playbook(playbook: Dict[str, Any]) -> Dict[str, Any]:
    """Accepte les clés YAML et les clés normalisées par l'API."""
    if not isinstance(playbook, dict):
        return {"Technique": "Playbook", "Goal": "", "Recommended Actions": []}

    def pick(*keys: str, default: Any = "") -> Any:
        for key in keys:
            if key in playbook and playbook[key] not in (None, ""):
                return playbook[key]
        return default

    return {
        **playbook,
        "Technique": pick("Technique", "technique", "name", "title", default="Playbook marketing"),
        "Goal": pick("Goal", "goal", "objectif", default=""),
        "When to use": pick("When to use", "when_to_use", "when", default=""),
        "Recommended Actions": pick(
            "Recommended Actions", "recommended_actions", "actions", default=[]
        ),
        "KPIs": pick("KPIs", "kpis", default=[]),
    }


def render_navigation(api_ok: bool) -> str:
    top_nav(api_ok)
    current = st.session_state.page
    columns = st.columns(len(PAGES))
    for index, page_name in enumerate(PAGES):
        with columns[index]:
            if st.button(
                page_name,
                key=f"nav_{index}_{page_name}",
                width="stretch",
                type="primary" if page_name == current else "secondary",
            ):
                st.session_state.page = page_name
                st.rerun()
    return st.session_state.page


def render_company_overview(companies: List[Dict[str, Any]]) -> None:
    page_header(
        "Vue d’ensemble",
        "Une vue opérationnelle des jeux de données et de la dernière décision produite par Eleva.",
    )

    result = st.session_state.last_result
    total_rows = sum(
        int(count)
        for company in companies
        for count in company.get("counts", {}).values()
        if isinstance(count, int)
    )
    latest_recos = len((result or {}).get("recommendations", []))

    cols = st.columns(4)
    with cols[0]:
        kpi_card("Entreprises", len(companies), "jeux")
    with cols[1]:
        kpi_card("Données chargées", total_rows, "lignes")
    with cols[2]:
        kpi_card("Analyses disponibles", len(st.session_state.history), "cycles")
    with cols[3]:
        kpi_card("Recommandations", latest_recos, "dernière analyse")

    if not companies:
        empty_state(
            "Aucun jeu de données",
            "Commencez par importer un fichier Customers, Orders ou Campaigns pour créer un espace entreprise.",
            "＋",
        )
        return

    st.markdown('<div class="h2">Jeux de données disponibles</div>', unsafe_allow_html=True)
    dataset_rows = []
    for company in companies:
        counts = company.get("counts", {})
        dataset_rows.append(
            {
                "Entreprise": company.get("name", company.get("company_id")),
                "Identifiant": company.get("company_id"),
                "Entités": ", ".join(company.get("entities", [])) or "—",
                "Lignes": sum(v for v in counts.values() if isinstance(v, int)),
                "Statut": "Prête à analyser" if company.get("entities") else "Vide",
            }
        )
    st.dataframe(pd.DataFrame(dataset_rows), width="stretch", hide_index=True)

    if result:
        st.markdown('<div class="h2">Dernière analyse</div>', unsafe_allow_html=True)
        info_cols = st.columns([2, 1, 1, 1])
        with info_cols[0]:
            st.markdown(
                f'<div class="card"><div class="kpi-label">Entreprise analysée</div>'
                f'<div style="font-size:1.25rem;font-weight:700">{html.escape(str(result.get("company_name") or result.get("company_id") or "—"))}</div>'
                f'<div style="color:{TEXT_MUTED};margin-top:.35rem">{html.escape(str(result.get("industry") or "Secteur non renseigné"))}</div></div>',
                unsafe_allow_html=True,
            )
        with info_cols[1]:
            kpi_card("Signaux détectés", len(result.get("issues", [])))
        with info_cols[2]:
            kpi_card("Playbooks", len(result.get("playbooks", [])))
        with info_cols[3]:
            kpi_card("Recommandations", latest_recos)

        if st.button("Voir les résultats", type="primary"):
            st.session_state.page = "Résultats"
            st.rerun()


def render_import() -> None:
    page_header(
        "Importer des données",
        "Chargez des CSV d’e-commerce sans imposer de noms de colonnes rigides.",
    )
    st.markdown(
        '<div class="card"><strong>Pipeline d’import V1</strong><br>'
        '<span style="color:#64748B">Mapping des colonnes → nettoyage → validation → stockage local par entreprise.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    companies = list_companies()
    existing_ids = [company["company_id"] for company in companies]
    mode = st.radio("Destination", ["Entreprise existante", "Nouvelle entreprise"], horizontal=True)

    if mode == "Entreprise existante" and existing_ids:
        company_id = st.selectbox("Entreprise", existing_ids)
    elif mode == "Entreprise existante":
        st.info("Aucune entreprise existante : saisissez un nouvel identifiant ci-dessous.")
        company_id = st.text_input("Identifiant entreprise", value="company_003").strip()
    else:
        company_id = st.text_input("Nouvel identifiant", value="company_003").strip()

    entity_label = st.selectbox(
        "Type de données",
        ["Customers (clients)", "Orders (commandes)", "Campaigns (campagnes)"],
    )
    entity = {
        "Customers (clients)": "customers",
        "Orders (commandes)": "orders",
        "Campaigns (campagnes)": "campaigns",
    }[entity_label]

    hints = {
        "customers": "Un identifiant client est nécessaire. Le nom de la colonne peut être libre.",
        "orders": "Un identifiant de commande et un identifiant client sont nécessaires.",
        "campaigns": "Les colonnes utiles sont conservées selon le schéma de campagnes du projet.",
    }
    st.caption(hints[entity])
    uploaded = st.file_uploader("Fichier CSV", type=["csv"])

    if uploaded is not None:
        try:
            text = uploaded.getvalue().decode("utf-8-sig", errors="replace")
            headers = next(csv.reader(StringIO(text)), [])
            if headers:
                st.markdown("**Colonnes détectées**")
                st.code(" · ".join(headers))
        except Exception:
            st.warning("Impossible de lire l’aperçu des colonnes.")

    if st.button("Importer et valider", type="primary", width="stretch"):
        if not company_id:
            st.error("Saisissez un identifiant d’entreprise.")
        elif uploaded is None:
            st.error("Sélectionnez un fichier CSV.")
        else:
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            safe_name = Path(uploaded.name).name
            tmp_path = upload_dir / f"{company_id}_{entity}_{safe_name}"
            tmp_path.write_bytes(uploaded.getvalue())

            company_dir = Path(settings.data_dir) / company_id
            company_dir.mkdir(parents=True, exist_ok=True)
            profile_path = company_dir / "profile.json"
            if not profile_path.exists():
                profile_path.write_text(
                    json.dumps(
                        {
                            "company_id": company_id,
                            "name": company_id,
                            "industry": "retail",
                            "current_focus": "general",
                            "goals": [],
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

            try:
                with st.spinner("Mapping, nettoyage et validation en cours…"):
                    imported = import_csv(
                        file_path=tmp_path,
                        entity=entity,
                        company_id=company_id,
                        write=True,
                    )
                report = imported.get("report", {})
                st.success(
                    f"Import terminé : {report.get('accepted_count', 0)} ligne(s) acceptée(s)."
                )
                st.json(report)
            except Exception as exc:
                st.error(f"Échec de l’import : {exc}")


def render_analyse(api_ok: bool) -> None:
    page_header(
        "Nouvelle analyse",
        "Choisissez une entreprise et une question : Eleva exécute ensuite le même Decision Engine séquentiel.",
    )
    if not api_ok:
        st.error(
            "L’API est hors ligne. Lancez-la depuis la racine : "
            "uvicorn api.main:app --reload --port 8000"
        )

    companies = list_companies()
    if not companies:
        empty_state(
            "Aucune donnée à analyser",
            "Importez au moins un fichier Customers ou Orders avant de lancer une analyse.",
            "⌁",
        )
        return

    with st.form("analysis_form"):
        left, right = st.columns([1, 1.4])
        with left:
            labels = {
                company["company_id"]: (
                    f"{company.get('name', company['company_id'])} · "
                    f"{', '.join(company.get('entities', [])) or 'vide'}"
                )
                for company in companies
            }
            company_id = st.selectbox(
                "Jeu de données",
                [company["company_id"] for company in companies],
                format_func=lambda value: labels.get(value, value),
            )
            max_rec = st.slider("Nombre de recommandations", 1, 5, 3)
        with right:
            selected_label = st.selectbox("Question métier", list(ANALYSIS_CHOICES.keys()))
            st.caption(
                "La question oriente le contexte envoyé au moteur, mais les étapes Understand → Recommend restent les mêmes."
            )

        launch = st.form_submit_button(
            "Lancer l’analyse",
            type="primary",
            width="stretch",
        )

    if launch:
        if not api_ok:
            st.error("Impossible de contacter l’agent.")
            return
        try:
            with st.spinner("Eleva observe, détecte, récupère, raisonne et recommande…"):
                result = call_analyze(company_id, ANALYSIS_CHOICES[selected_label], max_rec)
            st.session_state.last_result = result
            st.session_state.history.append(
                {
                    "company": result.get("company_name") or company_id,
                    "question": selected_label,
                }
            )
            st.session_state.page = "Résultats"
            st.rerun()
        except Exception as exc:
            st.error(f"Erreur lors de l’analyse : {exc}")


def render_results() -> None:
    page_header(
        "Résultats de l’analyse",
        "Les faits observés, les signaux détectés, les connaissances mobilisées et les recommandations finales.",
    )
    result = st.session_state.last_result
    if not result:
        empty_state(
            "Aucun résultat",
            "Lancez une analyse pour alimenter cette page.",
            "◌",
        )
        return

    st.markdown(
        f'<div class="card"><strong>{html.escape(str(result.get("company_name") or result.get("company_id") or "—"))}</strong>'
        f'<span style="color:{TEXT_MUTED}"> · {html.escape(str(result.get("industry") or "Secteur non renseigné"))}</span>'
        f'<br><span style="color:{TEXT_MUTED};font-size:.85rem">Étape retournée par l’API : {html.escape(str(result.get("current_step") or "—"))}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="h2">Indicateurs clés</div>', unsafe_allow_html=True)
    kpis = result.get("kpis", [])
    if kpis:
        columns = st.columns(4)
        for index, item in enumerate(kpis[:12]):
            with columns[index % 4]:
                kpi_card(item.get("name", ""), item.get("value"), item.get("unit") or "")
    else:
        st.info("Aucun KPI n’a été retourné par l’API.")

    st.markdown('<div class="h2">Segmentation RFM</div>', unsafe_allow_html=True)
    segments = result.get("segments", [])
    if segments:
        segment_df = pd.DataFrame(segments).rename(
            columns={"name": "Segment", "size": "Clients", "percentage": "Part (%)"}
        )
        st.dataframe(segment_df, width="stretch", hide_index=True)
    else:
        st.info("Aucun segment n’a été retourné.")

    st.markdown('<div class="h2">Observations et signaux</div>', unsafe_allow_html=True)
    insights = result.get("insights", [])
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.caption("Aucun insight textuel retourné.")

    st.markdown('<div class="h2">Problèmes et opportunités</div>', unsafe_allow_html=True)
    issues = result.get("issues", [])
    if issues:
        for issue in issues:
            issue_card(issue)
    else:
        st.info("Aucun problème ou opportunité n’a été détecté.")

    st.markdown('<div class="h2">Playbooks mobilisés par le RAG</div>', unsafe_allow_html=True)
    playbooks = result.get("playbooks", [])
    if playbooks:
        columns = st.columns(2)
        for index, playbook in enumerate(playbooks):
            with columns[index % 2]:
                playbook_card(normalize_playbook(playbook))
    else:
        st.info("Aucun playbook n’a été retourné par l’API.")

    st.markdown('<div class="h2">Recommandations finales</div>', unsafe_allow_html=True)
    recommendations = result.get("recommendations", [])
    if recommendations:
        for recommendation in recommendations:
            recommendation_card(recommendation)
    else:
        st.info("Aucune recommandation n’a été retournée.")


def render_clients() -> None:
    page_header(
        "Clients et actions personnalisées",
        "RFM et règles métier au niveau client ; le LLM reste réservé à la stratégie entreprise.",
    )
    result = st.session_state.last_result
    if not result:
        empty_state("Aucune analyse disponible", "Lancez une analyse avant d’explorer les clients.", "◎")
        return

    companies = list_companies()
    company_id = result.get("company_id")
    meta = company_meta(company_id, companies)
    if meta is not None and not meta.get("has_customers"):
        st.warning("Ce jeu de données ne contient pas de Customers.")
        return

    from services.client_recommendations import (
        build_strategic_notes_from_analysis,
        recommend_for_customers,
    )

    company_dir = Path(settings.data_dir) / company_id
    customers = read_json(company_dir / "customers.json", [])
    orders = read_json(company_dir / "orders.json", [])
    if not isinstance(customers, list):
        customers = []
    if not isinstance(orders, list):
        orders = []

    recommendations = recommend_for_customers(
        customers,
        orders,
        strategic_notes=build_strategic_notes_from_analysis(result),
    )
    if not recommendations:
        st.info("Aucun client exploitable n’a été trouvé dans ce jeu de données.")
        return

    df = pd.DataFrame(recommendations)
    filter_cols = st.columns(3)
    with filter_cols[0]:
        search = st.text_input("Rechercher un client", placeholder="ID client")
    with filter_cols[1]:
        segment_values = ["Tous"] + sorted(str(value) for value in df["segment"].dropna().unique())
        selected_segment = st.selectbox("Segment RFM", segment_values)
    with filter_cols[2]:
        priority_values = ["Toutes"] + sorted(str(value) for value in df["priorite"].dropna().unique())
        selected_priority = st.selectbox("Priorité", priority_values)

    if search:
        df = df[df["customer_id"].astype(str).str.contains(search, case=False, na=False)]
    if selected_segment != "Tous":
        df = df[df["segment"] == selected_segment]
    if selected_priority != "Toutes":
        df = df[df["priorite"] == selected_priority]

    metric_cols = st.columns(3)
    with metric_cols[0]:
        kpi_card("Clients affichés", len(df))
    with metric_cols[1]:
        kpi_card("Priorité élevée", int((df["priorite"] == "Élevée").sum()))
    with metric_cols[2]:
        kpi_card("Segments", int(df["segment"].nunique()) if not df.empty else 0)

    display_map = {
        "customer_id": "ID client",
        "segment": "Segment RFM",
        "r_score": "Score R",
        "f_score": "Score F",
        "m_score": "Score M",
        "recency_days": "Récence (j)",
        "frequency": "Fréquence",
        "monetary": "Montant",
        "priorite": "Priorité",
        "action": "Action recommandée",
        "playbook": "Playbook",
        "raison": "Justification",
    }
    if df.empty:
        st.info("Aucun client ne correspond aux filtres.")
    else:
        shown_columns = [column for column in display_map if column in df.columns]
        st.dataframe(
            df[shown_columns].rename(columns=display_map),
            width="stretch",
            hide_index=True,
        )

    st.markdown('<div class="h2">Stratégies entreprise</div>', unsafe_allow_html=True)
    st.caption("Ces recommandations proviennent du Decision Engine et nécessitent une validation humaine.")
    for recommendation in result.get("recommendations", []):
        recommendation_card(recommendation)


def render_statistics() -> None:
    page_header(
        "Statistiques",
        "Visualisations simples des valeurs retournées par la dernière analyse.",
    )
    result = st.session_state.last_result
    if not result:
        empty_state("Aucune statistique", "Lancez une analyse pour générer des visualisations.", "▥")
        return

    numeric = {}
    ratios = {}
    for item in result.get("kpis", []):
        name = item.get("name", "")
        value = item.get("value")
        if not isinstance(value, (int, float)):
            continue
        if item.get("unit") == "ratio" or "rate" in name or "ratio" in name:
            ratios[name] = float(value)
        else:
            numeric[name] = value

    if numeric:
        st.markdown('<div class="h2">Valeurs numériques</div>', unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame({"Valeur": numeric}))
    if ratios:
        st.markdown('<div class="h2">Ratios</div>', unsafe_allow_html=True)
        st.bar_chart(pd.DataFrame({"Taux": ratios}))
    segments = result.get("segments", [])
    if segments:
        st.markdown('<div class="h2">Taille des segments RFM</div>', unsafe_allow_html=True)
        segment_chart = {
            item.get("name", "Segment"): item.get("size", 0) for item in segments
        }
        st.bar_chart(pd.DataFrame({"Clients": segment_chart}))
    if not numeric and not ratios and not segments:
        st.info("Aucune valeur numérique ou segmentation à visualiser.")


def render_guides() -> None:
    page_header(
        "Guides marketing",
        "Base de connaissances locale utilisée par le module RAG pour cadrer les stratégies.",
    )
    try:
        playbooks = [normalize_playbook(item) for item in load_playbooks()]
    except Exception as exc:
        st.error(f"Impossible de charger les playbooks : {exc}")
        return

    if not playbooks:
        empty_state("Aucun guide", "Ajoutez des fichiers YAML dans knowledge/playbooks.", "▤")
        return

    st.caption(f"{len(playbooks)} guide(s) YAML chargé(s) depuis la base de connaissances.")
    columns = st.columns(2)
    for index, playbook in enumerate(playbooks):
        with columns[index % 2]:
            playbook_card(playbook)
            source = playbook.get("_source_file")
            if source:
                st.caption(f"Source : {source}")


def render_explanation() -> None:
    page_header(
        "Explicabilité",
        "Une lecture humaine des signaux, des problèmes, des playbooks et des prochaines étapes.",
    )
    result = st.session_state.last_result
    explanation = (result or {}).get("explanation")
    if not explanation:
        empty_state("Aucune explication", "Lancez une analyse pour produire une trace explicative.", "?")
        return

    title = explanation.get("recommendation_title") or "Décision Eleva"
    priority = str(explanation.get("priority") or "medium").lower()
    st.markdown(
        f'<div class="card"><div class="h3">{html.escape(str(title))}</div>'
        f'{badge(priority.upper(), "badge-primary")} '
        f'<span style="color:{TEXT_MUTED}">Statut : en attente d’approbation</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="h2">Pourquoi cette recommandation ?</div>', unsafe_allow_html=True)
    st.write(explanation.get("narrative") or "Aucun récit explicatif retourné.")

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="h2">Signaux observés</div>', unsafe_allow_html=True)
        for signal in explanation.get("signals", [])[:20]:
            st.markdown(f"- {signal}")
    with right:
        st.markdown('<div class="h2">Prochaines étapes</div>', unsafe_allow_html=True)
        for step in explanation.get("next_steps", []):
            st.markdown(f"- {step}")

    st.markdown('<div class="h2">Problèmes détectés</div>', unsafe_allow_html=True)
    for issue in explanation.get("detected_issues", []):
        issue_card(issue)

    st.markdown('<div class="h2">Playbooks mobilisés</div>', unsafe_allow_html=True)
    for playbook in explanation.get("playbooks_used", []):
        normalized = normalize_playbook(playbook)
        st.markdown(
            f"- **{normalized.get('Technique')}**"
            + (f" — {playbook.get('for_issue')}" if playbook.get("for_issue") else "")
        )

    gdpr_note = explanation.get("gdpr_note")
    if gdpr_note:
        st.info(gdpr_note)


api_ok = api_healthy()
page = render_navigation(api_ok)
companies = list_companies()

if page == "Vue d’ensemble":
    render_company_overview(companies)
elif page == "Importer":
    render_import()
elif page == "Analyser":
    render_analyse(api_ok)
elif page == "Résultats":
    render_results()
elif page == "Clients":
    render_clients()
elif page == "Statistiques":
    render_statistics()
elif page == "Guides marketing":
    render_guides()
elif page == "Explication":
    render_explanation()

st.markdown(
    '<div style="text-align:center;color:#94A3B8;font-size:.75rem;margin:3rem 0 1rem">'
    'Eleva V1 · Agent de décision marketing · Validation humaine requise avant toute action</div>',
    unsafe_allow_html=True,
)

__all__ = ["call_analyze", "api_healthy"]

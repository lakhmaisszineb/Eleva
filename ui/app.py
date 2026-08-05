"""
Eleva – Interface Streamlit professionnelle (FR).

Lancer depuis la racine du projet :
    streamlit run ui/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os

from config import settings

import pandas as pd
import requests
import streamlit as st

from data.catalog import list_companies
from data.importer import import_csv
from ui.theme import CUSTOM_CSS
from ui.components import (
    inject_css,
    topbar,
    navbar,
    section_title,
    kpi_card,
    issue_card,
    reco_card,
    badge_priority,
)

API_BASE = os.getenv("ELEVA_API_URL", "http://127.0.0.1:8000")

PAGES = [
    "Tableau de bord",
    "Import",
    "Analyse",
    "Résultats",
    "Clients",
    "Statistiques",
    "Explication",
]

ANALYSIS_CHOICES = {
    "Vue d’ensemble – problèmes et actions prioritaires": (
        "Analyse la situation actuelle et propose les actions prioritaires."
    ),
    "Paniers abandonnés – récupération de ventes": (
        "Analyse surtout les paniers abandonnés et propose des actions de récupération prioritaires."
    ),
    "Churn et rétention – clients à risque": (
        "Analyse le risque de churn et la rétention, puis propose des actions prioritaires."
    ),
    "Fidélisation et taux de réachat": (
        "Analyse le taux de réachat et propose des actions de fidélisation prioritaires."
    ),
    "Nouveaux clients – conversion vers le 2e achat": (
        "Analyse les nouveaux clients et propose comment les convertir en clients récurrents."
    ),
    "Campagnes marketing – performance et ROI": (
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
    st.session_state.page = "Tableau de bord"
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "history" not in st.session_state:
    st.session_state.history = []


def api_healthy() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).status_code == 200
    except Exception:
        return False


def call_analyze(company_id: str, question: str, max_rec: int = 3) -> dict:
    r = requests.post(
        f"{API_BASE}/analyze",
        json={
            "company_id": company_id,
            "question": question,
            "max_recommendations": max_rec,
        },
        timeout=120,
    )
    if not r.ok:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"API {r.status_code}: {detail}")
    return r.json()


# ----- En-tête + navigation -----
ok = api_healthy()
topbar(ok)
page = navbar(PAGES)

# ===========================================================================
# TABLEAU DE BORD
# ===========================================================================
if page == "Tableau de bord":
    section_title("Tableau de bord")
    st.caption("Synthèse de la dernière analyse réalisée par Eleva.")

    result = st.session_state.last_result
    if not result:
        st.info(
            "Aucune analyse en mémoire. Ouvrez l’onglet **Analyse** pour lancer un cycle."
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="eleva-card"><div class="kpi-label">Entreprise</div>'
                f'<div class="kpi-value" style="font-size:1.1rem">'
                f'{result.get("company_name", "—")}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="eleva-card"><div class="kpi-label">Secteur</div>'
                f'<div class="kpi-value" style="font-size:1.1rem">'
                f'{result.get("industry", "—")}</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            n_issues = len(result.get("issues", []))
            st.markdown(
                f'<div class="eleva-card"><div class="kpi-label">Signaux détectés</div>'
                f'<div class="kpi-value">{n_issues}</div></div>',
                unsafe_allow_html=True,
            )
        with c4:
            n_rec = len(result.get("recommendations", []))
            st.markdown(
                f'<div class="eleva-card"><div class="kpi-label">Recommandations</div>'
                f'<div class="kpi-value">{n_rec}</div></div>',
                unsafe_allow_html=True,
            )

        section_title("Indicateurs clés")
        kpis = result.get("kpis", [])
        cols = st.columns(4)
        for i, k in enumerate(kpis[:8]):
            with cols[i % 4]:
                kpi_card(k.get("name", ""), k.get("value"), k.get("unit") or "")

        section_title("Recommandations prioritaires")
        for reco in result.get("recommendations", [])[:3]:
            reco_card(reco)

        if st.session_state.history:
            section_title("Historique (session)")
            for h in reversed(st.session_state.history[-5:]):
                st.markdown(
                    f"- {h.get('company')} · {str(h.get('question', ''))[:80]}…"
                )

# ===========================================================================
# IMPORT
# ===========================================================================
elif page == "Import":
    section_title("Import de données")
    st.caption(
        "Importez un CSV avec **n’importe quels noms de colonnes**. "
        "Eleva lit la première ligne, mappe les colonnes via LLM (ou alias), "
        "ne garde que les champs utiles, puis enregistre les données localement. "
        "Types V1 : Customers, Orders, Campaigns."
    )

    companies = list_companies()
    company_ids = [c["company_id"] for c in companies]

    mode = st.radio(
        "Destination",
        ["Entreprise existante", "Nouvelle entreprise"],
        horizontal=True,
    )

    if mode == "Entreprise existante":
        if not company_ids:
            st.warning("Aucune entreprise en base. Créez-en une nouvelle.")
            company_id = None
        else:
            company_id = st.selectbox("Entreprise", company_ids)
    else:
        company_id = st.text_input(
            "Nouvel identifiant (ex. company_003)",
            value="company_003",
            help="Nom du dossier sous data/sample_data/",
        ).strip()

    entity_label = st.selectbox(
        "Type de données",
        [
            "Customers (clients)",
            "Orders (commandes)",
            "Campaigns (campagnes)",
        ],
    )
    entity_map = {
        "Customers (clients)": "customers",
        "Orders (commandes)": "orders",
        "Campaigns (campagnes)": "campaigns",
    }
    entity = entity_map[entity_label]

    if entity == "customers":
        st.info(
            "Pour **Customers**, le fichier doit contenir au moins une colonne "
            "identifiant les clients (ex. ID, id_client, email, code client…). "
            "Le nom exact est libre : le LLM s’en charge."
        )
    elif entity == "orders":
        st.info(
            "Pour **Orders**, il faut pouvoir identifier la commande et le client "
            "(ex. n° commande + id client). Noms de colonnes libres."
        )

    uploaded = st.file_uploader("Fichier CSV", type=["csv"])

    if uploaded is not None:
        # Aperçu des colonnes détectées (première ligne)
        try:
            import csv
            from io import StringIO

            text = uploaded.getvalue().decode("utf-8-sig", errors="replace")
            reader = csv.reader(StringIO(text))
            headers = next(reader, [])
            if headers:
                st.caption("Colonnes détectées dans le fichier :")
                st.code(" | ".join(headers))
        except Exception:
            pass

    if st.button("Importer", type="primary", use_container_width=True):
        if not company_id:
            st.error("Choisissez ou saisissez une entreprise.")
        elif not uploaded:
            st.error("Sélectionnez un fichier CSV.")
        else:
            tmp_dir = Path("data/uploads")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / f"{company_id}_{entity}_{uploaded.name}"
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
                with st.spinner(
                    "Analyse des noms de colonnes (LLM) + nettoyage + enregistrement…"
                ):
                    result_import = import_csv(
                        file_path=tmp_path,
                        entity=entity,
                        company_id=company_id,
                        write=True,
                    )
                report = result_import["report"]
                st.success(
                    f"Import OK — {report.get('accepted_count', 0)} lignes "
                    f"({entity}) pour **{company_id}**"
                )
                st.markdown("**Mapping utilisé :**")
                st.json(report.get("mapping", {}))
                if report.get("ignored_columns"):
                    st.caption(
                        "Colonnes ignorées (non nécessaires) : "
                        + ", ".join(report["ignored_columns"])
                    )
                st.json(report)
            except Exception as e:
                st.error(f"Échec de l’import : {e}")
                st.warning(
                    "Vérifiez le **type de données** choisi et que le fichier "
                    "contient bien une colonne permettant d’identifier les enregistrements "
                    "(client, commande, etc.). Les noms de colonnes peuvent être quelconques."
                )

# ===========================================================================
# ANALYSE
# ===========================================================================
elif page == "Analyse":
    section_title("Nouvelle analyse")
    st.caption(
        "Eleva analyse l’ensemble des données chargées pour l’entreprise et propose "
        "des recommandations. Choisissez un type de demande ci-dessous."
    )

    if not ok:
        st.error(
            "L’agent est hors ligne. Démarrez l’API : "
            "`uvicorn api.main:app --reload --port 8000`"
        )

    type_demande = st.radio(
        "Type de demande",
        [
            "Lancer une analyse marketing",
            "Qui est Eleva ? / À propos",
        ],
        horizontal=True,
    )

    if type_demande.startswith("Qui est Eleva"):
        if st.button("Afficher la réponse", type="primary"):
            st.markdown(
                """
                <div class="eleva-card">
                    <strong>Eleva</strong> est un agent de décision pour le marketing
                    e-commerce et retail.
                    <br><br>
                    Il observe les données de l’entreprise (clients, commandes, campagnes),
                    calcule des indicateurs et une segmentation RFM,
                    détecte problèmes et opportunités,
                    consulte des playbooks marketing,
                    puis propose des <strong>recommandations argumentées</strong>.
                    <br><br>
                    Aucune action (email, publicité, publication) n’est exécutée sans
                    validation humaine (statut : en attente d’approbation).
                    <br><br>
                    Pour obtenir des recommandations métier, choisissez
                    <em>« Lancer une analyse marketing »</em>.
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        companies = list_companies()
        if companies:
            st.caption(
                "Jeux de données détectés : "
                + ", ".join(f"{c['company_id']} ({', '.join(c['entities'])})" for c in companies)
            )
        else:
            st.warning(
                f"Aucun jeu de données trouvé dans `{settings.data_dir}`. "
                "Importez un CSV ou vérifiez DATA_DIR dans `.env`."
            )
        with st.form("form_analyse"):
            col1, col2 = st.columns([1, 2])
            with col1:
                if not companies:
                    st.warning(
                        "Aucune donnée. Allez dans **Import** pour charger un CSV."
                    )
                    company_id = None
                else:
                    labels = {
                        c["company_id"]: (
                            f"{c['name']} ({c['company_id']}) — "
                            f"{', '.join(c['entities']) or 'vide'}"
                        )
                        for c in companies
                    }
                    company_id = st.selectbox(
                        "Jeu de données / entreprise",
                        [c["company_id"] for c in companies],
                        format_func=lambda cid: labels.get(cid, cid),
                    )
                    meta = next(
                        c for c in companies if c["company_id"] == company_id
                    )
                    st.caption(
                        f"Entités : {', '.join(meta['entities']) or 'aucune'}. "
                        f"Recos clients : "
                        f"{'oui' if meta['has_customers'] else 'non (pas de Customers)'}."
                    )
                max_rec = st.slider("Nombre de recommandations", 1, 5, 3)
            with col2:
                choix = st.selectbox(
                    "Question d’analyse",
                    list(ANALYSIS_CHOICES.keys()),
                )
                st.caption(
                    "L’analyse porte sur l’ensemble des données disponibles "
                    "pour cette entreprise."
                )

            launched = st.form_submit_button(
                "Lancer l’analyse",
                type="primary",
                use_container_width=True,
            )

        if launched:
            question = ANALYSIS_CHOICES[choix]
            if not company_id:
                st.error("Aucun jeu de données sélectionné.")
            elif not ok:
                st.error("Impossible de contacter l’agent.")
            else:
                with st.spinner("Eleva observe, détecte et raisonne…"):
                    try:
                        data = call_analyze(company_id, question, max_rec)
                        st.session_state.last_result = data
                        st.session_state.history.append(
                            {
                                "company": data.get("company_name"),
                                "question": choix,
                            }
                        )
                        st.success("Analyse terminée.")
                        st.session_state.page = "Résultats"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de l’analyse : {e}")

# ===========================================================================
# RÉSULTATS
# ===========================================================================
elif page == "Résultats":
    section_title("Résultats")
    result = st.session_state.last_result
    if not result:
        st.warning("Aucun résultat. Lancez une analyse.")
    else:
        st.markdown(
            f"**{result.get('company_name')}** · {result.get('industry')} · "
            f"étape : `{result.get('current_step')}`"
        )

        section_title("Indicateurs")
        cols = st.columns(4)
        for i, k in enumerate(result.get("kpis", [])):
            with cols[i % 4]:
                kpi_card(k.get("name", ""), k.get("value"), k.get("unit") or "")

        section_title("Segments RFM")
        segs = result.get("segments", [])
        if segs:
            sc = st.columns(min(4, len(segs)))
            for i, s in enumerate(segs):
                with sc[i % len(sc)]:
                    kpi_card(
                        s.get("name", ""),
                        f"{s.get('size')} ({s.get('percentage')} %)",
                    )

        section_title("Observations")
        for ins in result.get("insights", []):
            st.markdown(f"- {ins}")

        section_title("Problèmes et opportunités")
        for issue in result.get("issues", []):
            issue_card(issue)

        section_title("Playbooks utilisés")
        for pb in result.get("playbooks", []):
            st.markdown(
                f"- **{pb.get('technique')}** — _{pb.get('issue_title')}_"
            )

        section_title("Recommandations")
        for reco in result.get("recommendations", []):
            reco_card(reco)

# ===========================================================================
# CLIENTS
# ===========================================================================
elif page == "Clients":
    section_title("Clients & recommandations personnalisées")
    st.caption(
        "RFM déterministe + règles métier par segment. "
        "Le LLM intervient uniquement au niveau stratégique (recommandations entreprise). "
        "Aucune génération LLM par client."
    )

    result = st.session_state.last_result
    companies = list_companies()
    company_id = (result or {}).get("company_id") or "company_001"
    meta = next((c for c in companies if c["company_id"] == company_id), None)

    if not result:
        st.info("Lancez d’abord une analyse.")
    elif meta is not None and not meta.get("has_customers"):
        st.warning(
            "Ce jeu de données ne contient pas de **Customers**. "
            "La page Clients reste vide. "
            "Importez un CSV de type Customers ou analysez un dataset qui en contient."
        )
    else:
        from services.client_recommendations import (
            recommend_for_customers,
            build_strategic_notes_from_analysis,
        )

        data_dir = Path(settings.data_dir) / company_id
        customers, orders = [], []
        try:
            if (data_dir / "customers.json").exists():
                customers = json.loads(
                    (data_dir / "customers.json").read_text(encoding="utf-8")
                )
            if (data_dir / "orders.json").exists():
                orders = json.loads(
                    (data_dir / "orders.json").read_text(encoding="utf-8")
                )
        except Exception as e:
            st.warning(f"Lecture des données impossible : {e}")

        strategic_notes = build_strategic_notes_from_analysis(result)
        recos = recommend_for_customers(
            customers, orders, strategic_notes=strategic_notes
        )

        section_title("Synthèse des segments (dernière analyse)")
        segs = result.get("segments") or []
        if segs:
            st.dataframe(
                pd.DataFrame(segs).rename(
                    columns={
                        "name": "Segment",
                        "size": "Clients",
                        "percentage": "Part (%)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        section_title("Recommandations par client")
        if not recos:
            st.warning("Aucun client trouvé.")
        else:
            df = pd.DataFrame(recos)
            display_cols = {
                "customer_id": "ID client",
                "segment": "Segment RFM",
                "recency_days": "Récence (j)",
                "frequency": "Fréquence",
                "monetary": "Montant",
                "priorite": "Priorité",
                "action": "Action recommandée",
                "playbook": "Playbook",
                "raison": "Justification",
            }
            cols_keep = [c for c in display_cols if c in df.columns]
            df = df[cols_keep].rename(columns=display_cols)
            st.dataframe(df, use_container_width=True, hide_index=True)

            n_high = sum(1 for r in recos if r["priorite"] == "Élevée")
            st.markdown(
                f"**{len(recos)}** client(s) · **{n_high}** en priorité élevée · "
                f"moteur : RFM + règles (pas de LLM individuel)"
            )

        section_title("Stratégies entreprise (LLM + RAG)")
        st.caption("Niveau décisionnel Eleva — validation humaine requise.")
        for reco in result.get("recommendations", []):
            reco_card(reco)

# ===========================================================================
# STATISTIQUES
# ===========================================================================
elif page == "Statistiques":
    section_title("Statistiques")
    result = st.session_state.last_result
    if not result:
        st.info("Aucune donnée à visualiser. Lancez une analyse.")
    else:
        kpis = result.get("kpis", [])
        if kpis:
            section_title("Indicateurs numériques")
            chart_data = {}
            for k in kpis:
                name = k.get("name")
                val = k.get("value")
                if isinstance(val, (int, float)) and k.get("unit") != "ratio":
                    chart_data[name] = val
            if chart_data:
                st.bar_chart(pd.DataFrame({"valeur": chart_data}))

            ratios = {
                k["name"]: float(k["value"])
                for k in kpis
                if k.get("unit") == "ratio"
                and isinstance(k.get("value"), (int, float))
            }
            if ratios:
                section_title("Taux (ratios)")
                st.bar_chart(pd.DataFrame({"taux": ratios}))

        segs = result.get("segments", [])
        if segs:
            section_title("Répartition des segments RFM")
            sdf = pd.DataFrame(segs).set_index("name")["size"]
            st.bar_chart(sdf)

# ===========================================================================
# EXPLICATION
# ===========================================================================
elif page == "Explication":
    section_title("Explicabilité")
    st.caption("Transparence du raisonnement · conformité à l’esprit RGPD")

    result = st.session_state.last_result
    exp = (result or {}).get("explanation")
    if not exp:
        st.warning("Aucune explication disponible. Lancez une analyse.")
    else:
        st.markdown(f"### {exp.get('recommendation_title', '')}")
        st.markdown(
            badge_priority(exp.get("priority", "medium"))
            + " &nbsp; Statut : en attente d’approbation",
            unsafe_allow_html=True,
        )

        st.markdown("#### Pourquoi cette recommandation ?")
        st.write(exp.get("narrative", ""))

        st.markdown("#### Signaux observés")
        for s in exp.get("signals", [])[:15]:
            st.markdown(f"- {s}")

        st.markdown("#### Problèmes et opportunités")
        for issue in exp.get("detected_issues", []):
            issue_card(issue)

        st.markdown("#### Playbooks mobilisés")
        for pb in exp.get("playbooks_used", []):
            st.markdown(
                f"- **{pb.get('technique')}** — {pb.get('for_issue')}"
            )

        st.markdown("#### Prochaines étapes")
        for step in exp.get("next_steps", []):
            st.markdown(f"→ {step}")

        st.info(exp.get("gdpr_note", ""))
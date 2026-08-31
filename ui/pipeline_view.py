"""
Renders a full DecisionState (result of DecisionEngine.run) in a clear,
non-technical way, reusable from the Analysis page and the Dashboard.
"""

from typing import Any, Dict

import streamlit as st
import plotly.express as px

from core.models import DecisionState
from engine.explain import explain_recommendation
from ui.components import (
    section_title, caption, kpi_grid, priority_badge, issue_type_badge,
    status_badge, empty_state, pipeline_stepper, quote_block,
)
from ui.theme import COLORS

KPI_LABELS_FR = {
    "total_customers": "Clients au total",
    "total_orders": "Commandes au total",
    "completed_orders": "Commandes complétées",
    "abandoned_orders": "Paniers abandonnés",
    "cart_abandonment_rate": "Taux d'abandon de panier",
    "average_order_value": "Panier moyen",
    "repeat_purchase_rate": "Taux de réachat",
    "approx_clv": "Valeur vie client (estimée)",
    "high_churn_risk_count": "Clients à risque élevé de churn",
}


def _is_fallback(recommendation) -> bool:
    just = (recommendation.justification or "").lower()
    return "fallback" in just or "indisponible" in just


def render_decision_state(state: DecisionState) -> None:
    if state.errors and not state.recommendations:
        return  # handled by caller (error banner)

    pipeline_stepper(completed=True)

    # ----- Company context recap -----
    if state.company_context:
        ctx = state.company_context
        st.markdown(
            f"**{ctx.name}** · secteur : {ctx.industry}"
            + (f" · objectif actuel : *{ctx.current_focus}*" if ctx.current_focus else "")
        )

    # ----- KPIs -----
    section_title("Indicateurs clés")
    if state.observation:
        kpi_grid(
            [k.model_dump() for k in state.observation.kpis],
            KPI_LABELS_FR,
        )
    else:
        empty_state("Aucune observation disponible.")

    # ----- RFM segments -----
    section_title("Segmentation client (RFM)")
    if state.observation and state.observation.segments:
        col_chart, col_list = st.columns([1.1, 1])
        with col_chart:
            segs = state.observation.segments
            fig = px.pie(
                names=[s.name for s in segs],
                values=[s.size for s in segs],
                hole=0.55,
                color_discrete_sequence=[
                    COLORS["navy"], COLORS["accent"], COLORS["sage"],
                    COLORS["amber"], COLORS["brick"], COLORS["gray"],
                    COLORS["navy_light"],
                ],
            )
            fig.update_traces(textinfo="percent+label", textfont_size=11)
            fig.update_layout(
                showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320,
            )
            st.plotly_chart(fig, use_container_width=True)
        with col_list:
            for s in sorted(state.observation.segments, key=lambda x: -x.size):
                st.markdown(f"**{s.name}** — {s.size} clients ({s.percentage}%)")
    else:
        empty_state("Segmentation RFM non disponible.")

    # ----- Insights -----
    if state.observation and state.observation.raw_insights:
        section_title("Constats principaux")
        for insight in state.observation.raw_insights:
            st.markdown(f"- {insight}")

    # ----- Detected issues -----
    section_title("Problèmes et opportunités détectés")
    if state.detected_issues:
        priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues_sorted = sorted(
            state.detected_issues, key=lambda i: priority_rank.get(i.priority.value, 9)
        )
        for issue in issues_sorted:
            with st.container():
                st.markdown(
                    f'<div class="eleva-card">'
                    f'<div>{issue_type_badge(issue.type.value)} {priority_badge(issue.priority.value)}</div>'
                    f'<h4 style="margin:0.4rem 0 0.2rem 0;">{issue.title}</h4>'
                    f'<p style="margin:0 0 0.3rem 0;">{issue.description}</p>'
                    + (
                        '<p class="eleva-caption">Preuves : ' + " · ".join(issue.evidence) + '</p>'
                        if issue.evidence else ""
                    )
                    + '</div>',
                    unsafe_allow_html=True,
                )
    else:
        empty_state("Aucun problème ni opportunité détecté sur cette analyse.")

    # ----- Playbooks -----
    section_title("Bonnes pratiques marketing mobilisées")
    if state.retrieved_playbooks:
        by_issue: Dict[str, list] = {}
        for pb in state.retrieved_playbooks:
            by_issue.setdefault(pb["issue_title"], []).append(pb)
        for issue_title, pbs in by_issue.items():
            with st.expander(f"{issue_title} — {len(pbs)} technique(s) associée(s)"):
                for pb in pbs:
                    st.markdown(f"**{pb['technique']}**")
                    st.markdown(f'<span class="eleva-caption">{pb["content"]}</span>', unsafe_allow_html=True)
                    st.markdown("---")
    else:
        empty_state("Aucune technique de la base de connaissances n'a été mobilisée.")

    # ----- Recommendations -----
    section_title("Recommandations finales")
    if state.recommendations:
        if any(_is_fallback(r) for r in state.recommendations):
            st.info(
                "L'assistant IA n'a pas pu être contacté pour cette analyse : "
                "les recommandations ci-dessous ont été générées par les règles de secours "
                "d'Eleva, à partir des mêmes observations et problèmes détectés."
            )
        for rec in state.recommendations:
            with st.container():
                st.markdown(
                    f'<div class="eleva-card">'
                    f'<div>{priority_badge(rec.priority.value)} {status_badge(rec.status.value)}</div>'
                    f'<h4 style="margin:0.4rem 0 0.2rem 0;">{rec.title}</h4>'
                    f'<p style="margin:0 0 0.4rem 0;">{rec.summary}</p>'
                    f'<p class="eleva-caption"><em>{rec.justification}</em></p>'
                    + (
                        '<p style="margin-top:0.5rem;"><strong>Prochaines étapes :</strong> '
                        + " · ".join(rec.next_steps) + '</p>'
                        if rec.next_steps else ""
                    )
                    + '</div>',
                    unsafe_allow_html=True,
                )

        section_title("Pourquoi cette recommandation ?")
        rec_titles = {r.id: f"{r.title} ({r.priority.value})" for r in state.recommendations}
        selected_id = st.selectbox(
            "Choisir une recommandation à expliquer",
            options=list(rec_titles.keys()),
            format_func=lambda rid: rec_titles[rid],
        )
        explanation = explain_recommendation(state, selected_id)
        st.session_state["explanation"] = explanation
        render_explanation(explanation)
    else:
        empty_state(
            "Aucune recommandation n'a pu être produite. "
            "Cela peut arriver si aucun problème ni opportunité significatif n'a été détecté."
        )


def render_explanation(explanation: Dict[str, Any]) -> None:
    if not explanation or explanation.get("error"):
        empty_state(explanation.get("error", "Explication indisponible.") if explanation else "Explication indisponible.")
        return

    quote_block(explanation["narrative"])

    with st.expander("Signaux observés utilisés dans ce raisonnement"):
        for s in explanation.get("signals", [])[:20]:
            st.markdown(f"- {s}")

    with st.expander("Hypothèses envisagées par Eleva"):
        hyps = explanation.get("hypotheses", [])
        if hyps:
            for h in hyps:
                st.markdown(f"- {h}")
        else:
            empty_state("Aucune hypothèse enregistrée.")

    caption(explanation.get("gdpr_note", ""))

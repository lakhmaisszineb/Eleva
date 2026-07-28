"""
Explainability module for Eleva.

Builds a human-readable explanation of why a recommendation was made,
based on the full DecisionState (observation, issues, playbooks, etc.).

Supports transparency and GDPR-oriented "right to explanation" principles.
"""

from typing import Optional, Dict, Any, List

from core.models import DecisionState, Recommendation
from config import get_logger

logger = get_logger(__name__)


def explain_recommendation(
    state: DecisionState,
    recommendation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a structured explanation for one recommendation.

    If recommendation_id is None, explains the first recommendation.
    """
    if not state.recommendations:
        return {
            "error": "Aucune recommandation à expliquer.",
            "recommendation_id": None,
        }

    rec: Recommendation
    if recommendation_id:
        rec = next(
            (r for r in state.recommendations if r.id == recommendation_id),
            state.recommendations[0],
        )
    else:
        rec = state.recommendations[0]

    # ----- Company context -----
    company = {}
    if state.company_context:
        company = {
            "name": state.company_context.name,
            "industry": state.company_context.industry,
            "focus": state.company_context.current_focus,
            "goals": state.company_context.goals,
        }

    # ----- Observation signals -----
    signals: List[str] = []
    if state.observation:
        for kpi in state.observation.kpis:
            unit = f" {kpi.unit}" if kpi.unit else ""
            signals.append(f"KPI {kpi.name} = {kpi.value}{unit}")
        for insight in state.observation.raw_insights:
            signals.append(f"Insight: {insight}")
        for seg in state.observation.segments:
            signals.append(
                f"Segment RFM '{seg.name}': {seg.size} clients ({seg.percentage}%)"
            )

    # ----- Related issues -----
    issues_explained = []
    for issue in state.detected_issues:
        issues_explained.append({
            "title": issue.title,
            "type": issue.type.value,
            "priority": issue.priority.value,
            "description": issue.description,
            "evidence": issue.evidence,
        })

    # ----- Playbooks used -----
    playbooks = [
        {
            "technique": pb.get("technique"),
            "for_issue": pb.get("issue_title"),
        }
        for pb in state.retrieved_playbooks
    ]

    # ----- Hypotheses (short) -----
    hypotheses = [h.statement for h in state.hypotheses]

    # ----- Strategies linked -----
    strategies = [
        {
            "name": s.name,
            "description": s.description,
            "playbooks": s.recommended_playbooks,
            "expected_impact": s.expected_impact,
            "effort": s.effort,
        }
        for s in rec.strategies
    ]

    # ----- Narrative (human-readable) -----
    narrative_parts = []

    if company:
        narrative_parts.append(
            f"Pour l'entreprise {company.get('name')} ({company.get('industry')}), "
            f"dont le focus actuel est « {company.get('focus')} »,"
        )

    narrative_parts.append(
        f"Eleva recommande : « {rec.title} »."
    )

    if state.observation and state.observation.raw_insights:
        narrative_parts.append(
            "Cette recommandation s'appuie sur les observations suivantes : "
            + " ; ".join(state.observation.raw_insights[:4])
            + "."
        )

    high_issues = [
        i.title for i in state.detected_issues if i.priority.value in ("high", "critical")
    ]
    if high_issues:
        narrative_parts.append(
            "Les problèmes prioritaires détectés sont : "
            + ", ".join(high_issues)
            + "."
        )

    pb_names = list({p["technique"] for p in playbooks if p.get("technique")})
    if pb_names:
        narrative_parts.append(
            "Les playbooks marketing mobilisés sont : "
            + ", ".join(pb_names)
            + "."
        )

    narrative_parts.append(
        f"Justification synthétique : {rec.justification}"
    )

    narrative_parts.append(
        "Cette recommandation est en statut « pending_approval » : "
        "aucune action n'est exécutée sans validation humaine."
    )

    explanation = {
        "recommendation_id": rec.id,
        "recommendation_title": rec.title,
        "recommendation_summary": rec.summary,
        "priority": rec.priority.value,
        "status": rec.status.value,
        "company": company,
        "user_question": state.request.question,
        "signals": signals,
        "detected_issues": issues_explained,
        "playbooks_used": playbooks,
        "hypotheses": hypotheses,
        "strategies": strategies,
        "expected_outcomes": rec.expected_outcomes,
        "next_steps": rec.next_steps,
        "narrative": " ".join(narrative_parts),
        "gdpr_note": (
            "Les données clients restent sous le contrôle de l'entreprise. "
            "Eleva expose le raisonnement pour garantir la transparence de la décision."
        ),
    }

    logger.info(f"[Explain] Explanation built for recommendation {rec.id}")
    return explanation


def format_explanation_for_display(explanation: Dict[str, Any]) -> str:
    """
    Turn the structured explanation into a readable text block.
    """
    if explanation.get("error"):
        return explanation["error"]

    lines = [
        "=" * 70,
        "EXPLICATION DE LA RECOMMANDATION",
        "=" * 70,
        f"Titre    : {explanation['recommendation_title']}",
        f"Priorité : {explanation['priority']}",
        f"Statut   : {explanation['status']}",
        "",
        "--- Pourquoi cette recommandation ? ---",
        explanation["narrative"],
        "",
        "--- Signaux observés (extrait) ---",
    ]

    for s in explanation.get("signals", [])[:12]:
        lines.append(f"  • {s}")

    lines.append("")
    lines.append("--- Problèmes / opportunités détectés ---")
    for issue in explanation.get("detected_issues", []):
        lines.append(
            f"  [{issue['priority'].upper()}] {issue['type']}: {issue['title']}"
        )
        for e in issue.get("evidence", [])[:3]:
            lines.append(f"      preuve: {e}")

    lines.append("")
    lines.append("--- Playbooks mobilisés ---")
    for pb in explanation.get("playbooks_used", []):
        lines.append(f"  • {pb.get('technique')}  (lié à: {pb.get('for_issue')})")

    lines.append("")
    lines.append("--- Prochaines étapes proposées ---")
    for step in explanation.get("next_steps", []):
        lines.append(f"  → {step}")

    lines.append("")
    lines.append(f"Note RGPD : {explanation.get('gdpr_note', '')}")
    lines.append("=" * 70)

    return "\n".join(lines)
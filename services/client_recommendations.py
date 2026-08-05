"""
Recommandations personnalisées par client (V1).

Approche hybride explicable :
- Segmentation RFM déterministe (services.rfm)
- Règles métier segment → action
- Enrichissement avec données client (recency, paniers abandonnés, churn…)
- AUCUN appel LLM par client
- AUCUN ML

Le LLM reste au niveau stratégique (Decision Engine).
"""

from typing import Any, Dict, List, Optional

from services.rfm import compute_rfm


# ---------------------------------------------------------------------------
# Règles métier : segment RFM → stratégie d'action
# (alignées sur les playbooks Eleva)
# ---------------------------------------------------------------------------

SEGMENT_STRATEGIES: Dict[str, Dict[str, str]] = {
    "Champions": {
        "action": "Upsell, offre exclusive ou programme de parrainage",
        "priorite": "Moyenne",
        "playbook": "Loyalty Program / Cross-sell",
        "template_raison": (
            "Segment Champions (R={r}, F={f}, M={m}) : client à forte valeur. "
            "À activer pour la croissance (upsell / parrainage)."
        ),
    },
    "Loyal": {
        "action": "Fidélisation et cross-sell ciblé",
        "priorite": "Moyenne",
        "playbook": "Loyalty Program",
        "template_raison": (
            "Segment Loyal (R={r}, F={f}, M={m}) : bon engagement. "
            "Maintenir la relation et augmenter le panier moyen."
        ),
    },
    "Potential Loyalist": {
        "action": "Nurturing pour renforcer la fidélité",
        "priorite": "Moyenne",
        "playbook": "Welcome Campaign / Loyalty Program",
        "template_raison": (
            "Segment Potential Loyalist (R={r}, F={f}, M={m}) : "
            "potentiel de fidélisation à développer."
        ),
    },
    "New / Promising": {
        "action": "Séquence de bienvenue + incitation au 2ᵉ achat",
        "priorite": "Moyenne",
        "playbook": "Welcome Campaign",
        "template_raison": (
            "Segment New / Promising (R={r}, F={f}, M={m}) : "
            "priorité conversion vers un second achat."
        ),
    },
    "At Risk": {
        "action": "Campagne de rétention / win-back personnalisée",
        "priorite": "Élevée",
        "playbook": "Churn Reduction / Win-back",
        "template_raison": (
            "Segment At Risk (R={r}, F={f}, M={m}) : "
            "activité en baisse, risque de churn. Action de rétention recommandée."
        ),
    },
    "Hibernating (high value)": {
        "action": "Relance prioritaire (forte valeur passée)",
        "priorite": "Élevée",
        "playbook": "Win-back / Reactivation Campaign",
        "template_raison": (
            "Segment Hibernating high value (R={r}, F={f}, M={m}) : "
            "inactif mais historique de valeur élevé."
        ),
    },
    "Lost / Churned": {
        "action": "Campagne de réactivation avec offre limitée",
        "priorite": "Moyenne",
        "playbook": "Win-back / Reactivation Campaign",
        "template_raison": (
            "Segment Lost / Churned (R={r}, F={f}, M={m}) : "
            "client très inactif. Tenter une réactivation ciblée."
        ),
    },
    "Need Attention": {
        "action": "Parcours personnalisé selon le comportement d’achat",
        "priorite": "Moyenne",
        "playbook": "RFM Analysis",
        "template_raison": (
            "Segment Need Attention (R={r}, F={f}, M={m}) : "
            "profil mixte, adapter le message au parcours."
        ),
    },
}

DEFAULT_STRATEGY = {
    "action": "Parcours personnalisé selon le profil RFM",
    "priorite": "Moyenne",
    "playbook": "RFM Analysis",
    "template_raison": (
        "Segment « {segment} » (R={r}, F={f}, M={m}) : "
        "appliquer la stratégie du segment défini par l’analyse RFM."
    ),
}


def _match_strategy(segment: str) -> Dict[str, str]:
    """Trouve la stratégie règles pour un label de segment RFM."""
    if segment in SEGMENT_STRATEGIES:
        return SEGMENT_STRATEGIES[segment]
    s = (segment or "").lower()
    for key, val in SEGMENT_STRATEGIES.items():
        if key.lower() in s or s in key.lower():
            return val
    return {**DEFAULT_STRATEGY, "template_raison": DEFAULT_STRATEGY["template_raison"]}


def recommend_for_customers(
    customers: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    strategic_notes: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Produit une recommandation par client.

    Étapes :
    1. RFM sur customers + orders
    2. Règle segment → action
    3. Surcouches client (abandon, churn score)
    4. (Optionnel) note stratégique issue du Decision Engine pour ce segment

    strategic_notes: { "At Risk": "texte stratégie LLM...", ... } optionnel
    """
    strategic_notes = strategic_notes or {}
    rfm_list = compute_rfm(customers, orders)
    rfm_by_id = {row["customer_id"]: row for row in rfm_list}

    abandoned_ids = {
        o.get("customer_id")
        for o in orders
        if o.get("status") == "abandoned" and o.get("customer_id")
    }

    results: List[Dict[str, Any]] = []

    for c in customers:
        cid = c.get("customer_id")
        rfm = rfm_by_id.get(cid, {})
        segment = rfm.get("rfm_segment") or c.get("segment") or "Need Attention"
        r_score = rfm.get("r_score", "—")
        f_score = rfm.get("f_score", "—")
        m_score = rfm.get("m_score", "—")
        recency = rfm.get("recency_days", c.get("days_since_last_order"))
        frequency = rfm.get("frequency", c.get("total_orders"))
        monetary = rfm.get("monetary", c.get("total_spent"))

        strategy = _match_strategy(str(segment))
        raison = strategy["template_raison"].format(
            segment=segment,
            r=r_score,
            f=f_score,
            m=m_score,
        )
        action = strategy["action"]
        priorite = strategy["priorite"]
        playbook = strategy["playbook"]

        # Surcouche : panier abandonné
        if cid in abandoned_ids:
            action = "Relance de panier abandonné (prioritaire)"
            priorite = "Élevée"
            playbook = "Abandoned Cart Recovery"
            raison = (
                f"Panier abandonné détecté. Segment RFM : {segment} "
                f"(R={r_score}, F={f_score}, M={m_score}). "
                f"Recency={recency} j, dépenses={monetary}."
            )

        # Surcouche : score de churn élevé (si fourni dans les données)
        churn = c.get("churn_risk_score")
        try:
            churn_f = float(churn) if churn is not None else None
        except (TypeError, ValueError):
            churn_f = None
        if (
            churn_f is not None
            and churn_f >= 0.7
            and "abandonné" not in action.lower()
        ):
            action = "Rétention urgente (score de churn élevé)"
            priorite = "Élevée"
            playbook = "Churn Reduction"
            raison = (
                f"Score de churn={churn_f:.2f}. Segment RFM : {segment} "
                f"(R={r_score}, F={f_score}, M={m_score})."
            )

        # Lien optionnel avec une stratégie LLM de segment (niveau stratégique)
        note = strategic_notes.get(segment)
        if note:
            raison = f"{raison} Stratégie segment : {note}"

        results.append({
            "customer_id": cid,
            "segment": segment,
            "r_score": r_score,
            "f_score": f_score,
            "m_score": m_score,
            "recency_days": recency,
            "frequency": frequency,
            "monetary": monetary,
            "priorite": priorite,
            "action": action,
            "playbook": playbook,
            "raison": raison,
        })

    priority_rank = {"Élevée": 0, "Moyenne": 1, "Faible": 2}
    results.sort(key=lambda x: (priority_rank.get(x["priorite"], 9), str(x["customer_id"])))
    return results


def build_strategic_notes_from_analysis(result: Dict[str, Any]) -> Dict[str, str]:
    """
    Extrait des notes stratégiques simples depuis la réponse /analyze
    (recommandations entreprise) pour enrichir le texte des recos clients.
    Pas d'appel LLM ici : simple rapprochement textuel.
    """
    notes: Dict[str, str] = {}
    recos = result.get("recommendations") or []
    mapping = [
        ("At Risk", ["churn", "rétention", "retention", "risque", "at risk"]),
        ("Lost / Churned", ["réactivation", "reactivation", "win-back", "winback", "perdus"]),
        ("New / Promising", ["bienvenue", "welcome", "nouveaux", "2e", "deuxième"]),
        ("Champions", ["vip", "champion", "parrainage", "upsell"]),
        ("Loyal", ["fidél", "loyalty", "réachat", "reachat"]),
    ]
    for reco in recos:
        text = " ".join([
            str(reco.get("title", "")),
            str(reco.get("summary", "")),
            str(reco.get("justification", "")),
        ]).lower()
        short = (reco.get("title") or reco.get("summary") or "")[:180]
        for segment, keys in mapping:
            if any(k in text for k in keys) and segment not in notes:
                notes[segment] = short
    return notes
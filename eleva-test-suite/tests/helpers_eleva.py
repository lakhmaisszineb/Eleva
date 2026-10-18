"""
Test helpers: a scriptable fake LLM and SYNTHETIC data builders.

Everything here is synthetic (invented company, invented customers). No real
or confidential data is used.
"""
import json
import re
from typing import Any, Callable, Dict, List, Union

# ---------------------------------------------------------------------------
# Synthetic dataset (hand-computable on purpose)
# ---------------------------------------------------------------------------
SYNTHETIC_PROFILE = {
    "name": "Synthetic Shop (TEST DATA)",
    "industry": "fashion",
    "description": "Synthetic company used only by the Eleva test-suite.",
    "goals": ["Reduce churn", "Reduce cart abandonment"],
    "current_focus": "retention",
    "metadata": {"currency": "EUR"},
}

SYNTHETIC_CUSTOMERS: List[Dict[str, Any]] = [
    {"customer_id": "c1", "total_orders": 12, "total_spent": 1200.0, "days_since_last_order": 5,   "churn_risk_score": 0.1,  "email": "c1@example.test", "segment": None},
    {"customer_id": "c2", "total_orders": 8,  "total_spent": 800.0,  "days_since_last_order": 20,  "churn_risk_score": 0.2,  "email": None, "segment": None},
    {"customer_id": "c3", "total_orders": 5,  "total_spent": 400.0,  "days_since_last_order": 60,  "churn_risk_score": 0.75, "email": None, "segment": None},
    {"customer_id": "c4", "total_orders": 3,  "total_spent": 150.0,  "days_since_last_order": 100, "churn_risk_score": 0.8,  "email": None, "segment": None},
    {"customer_id": "c5", "total_orders": 1,  "total_spent": 40.0,   "days_since_last_order": 200, "churn_risk_score": None, "email": None, "segment": None},
    {"customer_id": "c6", "total_orders": 1,  "total_spent": 30.0,   "days_since_last_order": 30,  "churn_risk_score": None, "email": None, "segment": None},
    {"customer_id": "c7", "total_orders": 0,  "total_spent": 0.0,    "days_since_last_order": None, "churn_risk_score": None, "email": None, "segment": None},
    {"customer_id": "c8", "total_orders": 2,  "total_spent": 90.0,   "days_since_last_order": 150, "churn_risk_score": 0.4,  "email": None, "segment": None},
]

SYNTHETIC_ORDERS: List[Dict[str, Any]] = [
    {"order_id": "o1", "customer_id": "c1", "status": "completed", "total": 100.0, "order_date": "2026-09-01"},
    {"order_id": "o2", "customer_id": "c1", "status": "completed", "total": 50.0,  "order_date": "2026-09-20"},
    {"order_id": "o3", "customer_id": "c2", "status": "completed", "total": 80.0,  "order_date": "2026-08-01"},
    {"order_id": "o4", "customer_id": "c3", "status": "abandoned", "total": 60.0,  "order_date": "2026-09-25"},
    {"order_id": "o5", "customer_id": "c4", "status": "abandoned", "total": 40.0,  "order_date": "2026-09-26"},
    {"order_id": "o6", "customer_id": "c5", "status": "cancelled", "total": 30.0,  "order_date": "2026-03-01"},
    {"order_id": "o7", "customer_id": "c2", "status": "completed", "total": 70.0,  "order_date": "2026-09-10"},
    {"order_id": "o8", "customer_id": "c6", "status": "refunded",  "total": 20.0,  "order_date": "2026-09-05"},
]

SYNTHETIC_CAMPAIGNS: List[Dict[str, Any]] = [
    {"campaign_id": "A", "name": "Camp A", "type": "email", "conversion_rate": 0.05, "roi": 3.0},
    {"campaign_id": "B", "name": "Camp B", "type": "email", "conversion_rate": 0.01, "roi": 1.0},
    {"campaign_id": "C", "name": "Camp C", "type": "ads",   "conversion_rate": 0.02, "roi": 1.5},
    {"campaign_id": "D", "name": "Camp D", "type": "ads",   "conversion_rate": None, "roi": None},
]

# Expected KPI values for the synthetic dataset (computed by hand, see tests):
#   completed = o1,o2,o3,o7 -> AOV = (100+50+80+70)/4 = 75.0
#   abandoned = o4,o5 -> 2/8 = 0.25 ; repeat: c1,c2 have 2 completed -> 2/2 = 1.0
#   CLV = 2710/8 = 338.75 ; high churn (>=0.7) = c3,c4 -> 2 ; low ROI (<1.5) = B only
EXPECTED_KPIS = {
    "total_customers": 8,
    "total_orders": 8,
    "completed_orders": 4,
    "abandoned_orders": 2,
    "cart_abandonment_rate": 0.25,
    "average_order_value": 75.0,
    "repeat_purchase_rate": 1.0,
    "approx_clv": 338.75,
    "high_churn_risk_count": 2,
    "low_roi_campaigns_count": 1,
    "low_roi_campaign_names": ["Camp B"],
}


def seed_company(
    company_id: str = "co_test",
    profile=SYNTHETIC_PROFILE,
    customers=SYNTHETIC_CUSTOMERS,
    orders=SYNTHETIC_ORDERS,
    campaigns=SYNTHETIC_CAMPAIGNS,
) -> str:
    """Write a synthetic company into the (already isolated) test DB."""
    from data.db import (
        get_connection, init_db, upsert_profile,
        replace_customers, replace_orders, replace_campaigns,
    )

    init_db()
    conn = get_connection()
    try:
        if profile is not None:
            upsert_profile(conn, company_id, dict(profile))
        replace_customers(conn, company_id, [dict(r) for r in customers])
        replace_orders(conn, company_id, [dict(r) for r in orders])
        replace_campaigns(conn, company_id, [dict(r) for r in campaigns])
        conn.commit()
    finally:
        conn.close()
    return company_id


# ---------------------------------------------------------------------------
# Fake LLM
# ---------------------------------------------------------------------------
Handler = Union[str, Exception, Callable[..., str]]


def _default_mapper(system: str, user: str) -> str:
    cols = re.findall(r"^- (.+)$", user.split("Schéma Eleva cible")[0], flags=re.M)
    fields = user.split("Schéma Eleva cible (champs autorisés):")[1].split("\n")[1]
    mapping = {f.strip(): (f.strip() if f.strip() in cols else None) for f in fields.split(",")}
    return json.dumps({"mapping": mapping, "ignored": [c for c in cols if c not in mapping.values()]})


def _default_reason(system: str, user: str) -> str:
    issues = re.findall(r"^- \[\w+\] \w+: (.+?) — ", user, flags=re.M)
    return json.dumps({"hypotheses": [
        {"issue_title": t, "statement": f"Hypothese pour {t}", "confidence": 0.8} for t in issues
    ]})


def _default_plan(system: str, user: str) -> str:
    return json.dumps({"strategies": [
        {"name": "Strategie 1", "description": "Desc 1", "playbooks": ["Win-back / Reactivation Campaign"],
         "expected_impact": "Eleve", "effort": "low", "main_risks": ["risque"]},
        {"name": "Strategie 2", "description": "Desc 2", "playbooks": [],
         "expected_impact": "Moyen", "effort": "medium", "main_risks": []},
    ]})


def _default_recommend(system: str, user: str) -> str:
    return json.dumps({"recommendations": [
        {"title": "Reco 1", "summary": "S1", "justification": "J1", "priority": "high",
         "expected_outcomes": ["o1"], "next_steps": ["n1"]},
        {"title": "Reco 2", "summary": "S2", "justification": "J2", "priority": "medium",
         "expected_outcomes": [], "next_steps": []},
    ]})


class FakeLLM:
    """Callable replacement for `llm.groq_client.chat` (signature-compatible)."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self._handlers: Dict[str, Handler] = {
            "mapper": _default_mapper,
            "reason": _default_reason,
            "plan": _default_plan,
            "recommend": _default_recommend,
        }

    def set(self, stage: str, handler: Handler) -> None:
        assert stage in self._handlers, f"unknown stage {stage}"
        self._handlers[stage] = handler

    def calls_for(self, stage: str):
        return [c for c in self.calls if c["stage"] == stage]

    def _stage(self, system: str) -> str:
        from data.importer.column_mapper import MAPPER_SYSTEM
        from llm.prompts import REASON_SYSTEM, PLAN_SYSTEM, RECOMMEND_SYSTEM

        for stage, prompt in (("mapper", MAPPER_SYSTEM), ("reason", REASON_SYSTEM),
                              ("plan", PLAN_SYSTEM), ("recommend", RECOMMEND_SYSTEM)):
            if system == prompt:
                return stage
        return "other"

    def __call__(self, system_prompt, user_prompt, history=None):
        stage = self._stage(system_prompt)
        self.calls.append({"stage": stage, "system": system_prompt, "user": user_prompt})
        if stage == "other":
            return "ok"
        handler = self._handlers[stage]
        if isinstance(handler, Exception):
            raise handler
        if callable(handler):
            return handler(system_prompt, user_prompt)
        return handler

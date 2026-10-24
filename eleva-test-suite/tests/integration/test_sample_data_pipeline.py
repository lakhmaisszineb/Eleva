"""Integration: the demo JSON files committed in data/sample_data/ (read-only) are migrated into a
TEMP database and run through the full pipeline with a fake LLM. Your real eleva.db is never opened."""
import json
from pathlib import Path

import pytest

from core.models import AnalysisRequest
from data.company_store import CompanyStore
from data.db import get_connection
from engine.decision_engine import DecisionEngine
from scripts.migrate_json_to_sqlite import migrate_company

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_data"
COMPANIES = sorted(p.name for p in SAMPLE_DIR.iterdir() if (p / "profile.json").exists()) if SAMPLE_DIR.exists() else []

pytestmark = pytest.mark.skipif(not COMPANIES, reason="no demo companies in data/sample_data")


def _migrate(company_id):
    conn = get_connection()
    stats = migrate_company(conn, company_id, SAMPLE_DIR)
    conn.commit(); conn.close()
    return stats


def _json(company_id, name):
    f = SAMPLE_DIR / company_id / name
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else []


@pytest.mark.parametrize("company_id", COMPANIES)
def test_demo_company_migrates_with_exact_row_counts(company_id):
    stats = _migrate(company_id)
    s = CompanyStore()
    assert stats["profile"] is True
    assert len(s.get_customers(company_id)) == len(_json(company_id, "customers.json"))
    assert len(s.get_orders(company_id)) == len(_json(company_id, "orders.json"))
    assert len(s.get_campaigns(company_id)) == len(_json(company_id, "campaigns.json"))


@pytest.mark.parametrize("company_id", COMPANIES)
def test_demo_company_runs_full_pipeline(company_id, fake_llm):
    _migrate(company_id)
    st = DecisionEngine().run(AnalysisRequest(company_id=company_id, question="Priorités ?", max_recommendations=3))
    assert st.errors == [] and st.current_step == "done"
    kpis = {k.name: k.value for k in st.observation.kpis}
    assert kpis["total_customers"] == len(_json(company_id, "customers.json"))
    assert st.recommendations and all(r.status.value == "pending_approval" for r in st.recommendations)


# @pytest.mark.xfail(strict=True, reason="DATA-1: in company_001 the 4 orders reference customer ids (c1..c4) that do not exist among the 350 customers (101..450), so order-based KPIs/RFM cannot be linked to customers")
def test_demo_orders_reference_existing_customers():
    for company_id in COMPANIES:
        cust = {c["customer_id"] for c in _json(company_id, "customers.json")}
        orders = _json(company_id, "orders.json")
        assert all(o["customer_id"] in cust for o in orders), company_id

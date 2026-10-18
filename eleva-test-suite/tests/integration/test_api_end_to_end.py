"""Integration: HTTP request -> FastAPI -> DecisionEngine -> SQLite + Chroma -> (fake LLM) -> JSON response."""
import pytest
from fastapi.testclient import TestClient

from helpers_eleva import seed_company, EXPECTED_KPIS


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


def test_analyze_full_flow_returns_complete_structured_response(client, seeded_company, fake_llm):
    r = client.post("/analyze", json={"company_id": "co_test", "question": "Priorités ?"})
    assert r.status_code == 200
    b = r.json()
    assert b["company_id"] == "co_test" and b["industry"] == "fashion" and b["current_step"] == "done"
    kpis = {k["name"]: k["value"] for k in b["kpis"]}
    assert kpis["total_customers"] == EXPECTED_KPIS["total_customers"] and kpis["average_order_value"] == 75.0
    assert b["segments"] and b["insights"] and b["issues"] and b["playbooks"]
    assert b["recommendations"] and {x["status"] for x in b["recommendations"]} == {"pending_approval"}
    assert b["explanation"]["recommendation_id"] == b["recommendations"][0]["id"]
    assert "validation humaine" in b["explanation"]["narrative"]
    assert b["errors"] == []


def test_analyze_unknown_company_returns_400(client, fake_llm):
    r = client.post("/analyze", json={"company_id": "ghost"})
    assert r.status_code == 400 and "Profile not found" in r.json()["detail"]["errors"][0]
    assert fake_llm.calls == []


def test_analyze_respects_max_recommendations(client, seeded_company, fake_llm):
    r = client.post("/analyze", json={"company_id": "co_test", "max_recommendations": 1})
    assert len(r.json()["recommendations"]) == 1


def test_analyze_survives_llm_outage_with_200_and_fallback(client, seeded_company, llm_down):
    r = client.post("/analyze", json={"company_id": "co_test"})
    assert r.status_code == 200
    assert all("fallback" in x["justification"].lower() for x in r.json()["recommendations"])


def test_analyze_two_companies_do_not_leak_into_each_other(client, fake_llm):
    seed_company("A")
    seed_company("B", profile={"name": "Only B", "industry": "food"},
                 customers=[{"customer_id": "b1", "total_orders": 1, "total_spent": 5.0}], orders=[], campaigns=[])
    a = client.post("/analyze", json={"company_id": "A"}).json()
    b = client.post("/analyze", json={"company_id": "B"}).json()
    assert {k["name"]: k["value"] for k in a["kpis"]}["total_customers"] == 8
    assert {k["name"]: k["value"] for k in b["kpis"]}["total_customers"] == 1
    assert b["company_name"] == "Only B"


def test_health_endpoint_needs_no_database_or_llm(client):
    assert client.get("/health").json()["status"] == "ok"

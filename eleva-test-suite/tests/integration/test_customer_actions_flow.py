"""Integration: store -> RFM -> per-customer rule engine (+ strategic notes from /analyze output).
Mirrors what ui/views.py does on the 'Clients' page. No LLM involved per customer."""
from data.company_store import CompanyStore
from services.client_recommendations import recommend_for_customers, build_strategic_notes_from_analysis
from services.rfm import compute_rfm


def test_every_stored_customer_gets_exactly_one_recommendation(seeded_company):
    s = CompanyStore()
    out = recommend_for_customers(s.get_customers("co_test"), s.get_orders("co_test"))
    assert sorted(r["customer_id"] for r in out) == [f"c{i}" for i in range(1, 9)]
    assert all(r["action"] and r["playbook"] and r["raison"] for r in out)


def test_business_overrides_apply_on_stored_data(seeded_company):
    s = CompanyStore()
    by_id = {r["customer_id"]: r for r in recommend_for_customers(s.get_customers("co_test"), s.get_orders("co_test"))}
    assert by_id["c3"]["playbook"] == "Abandoned Cart Recovery"        # abandoned order o4
    assert by_id["c4"]["playbook"] == "Abandoned Cart Recovery"        # abandoned (o5) wins over churn 0.8
    assert by_id["c1"]["playbook"] != "Abandoned Cart Recovery"
    assert all(by_id[c]["priorite"] == "Élevée" for c in ("c3", "c4"))


def test_high_priority_customers_are_listed_first(seeded_company):
    s = CompanyStore()
    out = recommend_for_customers(s.get_customers("co_test"), s.get_orders("co_test"))
    prios = [r["priorite"] for r in out]
    assert prios == sorted(prios, key=lambda p: {"Élevée": 0, "Moyenne": 1, "Faible": 2}[p])


def test_segments_from_rfm_match_segments_in_recommendations(seeded_company):
    s = CompanyStore()
    cust, orders = s.get_customers("co_test"), s.get_orders("co_test")
    rfm = {r["customer_id"]: r["rfm_segment"] for r in compute_rfm(cust, orders)}
    recs = {r["customer_id"]: r["segment"] for r in recommend_for_customers(cust, orders)}
    assert rfm == recs


def test_strategic_notes_from_an_analysis_result_enrich_matching_customers(seeded_company):
    s = CompanyStore()
    cust, orders = s.get_customers("co_test"), s.get_orders("co_test")
    analysis = {"recommendations": [{"title": "Plan de rétention churn", "summary": "", "justification": ""}]}
    notes = build_strategic_notes_from_analysis(analysis)
    assert notes == {"At Risk": "Plan de rétention churn"}
    out = recommend_for_customers(cust, orders, notes)
    for r in out:
        if r["segment"] == "At Risk":
            assert "Plan de rétention churn" in r["raison"]
        else:
            assert "Stratégie segment" not in r["raison"]

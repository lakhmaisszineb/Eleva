"""Unit tests: services/client_recommendations.py (rule-based per-customer actions, no LLM)."""
import pytest

from services import client_recommendations as cr


def _c(cid, **kw):
    return {"customer_id": cid, "total_orders": 0, "total_spent": 0, **kw}


def _o(cid, status="completed", total=10, date="2026-09-01"):
    return {"order_id": f"o-{cid}-{status}", "customer_id": cid, "status": status, "total": total, "order_date": date}


# ------------------------------ _match_strategy ------------------------------
def test_match_strategy_exact():
    assert cr._match_strategy("At Risk") is cr.SEGMENT_STRATEGIES["At Risk"]


def test_match_strategy_case_insensitive_substring():
    assert cr._match_strategy("champions") is cr.SEGMENT_STRATEGIES["Champions"]


def test_match_strategy_unknown_uses_default_with_segment_placeholder():
    s = cr._match_strategy("Totally New Label")
    assert s["playbook"] == "RFM Analysis" and "{segment}" in s["template_raison"]


def test_every_rfm_segment_produced_by_rfm_has_a_strategy():
    from services.rfm import _rfm_segment
    produced = {_rfm_segment(r, f, m) for r in range(1, 6) for f in range(1, 6) for m in range(1, 6)}
    assert produced <= set(cr.SEGMENT_STRATEGIES)


# --------------------------- recommend_for_customers -------------------------
def test_empty_customers_gives_empty_list():
    assert cr.recommend_for_customers([], []) == []


def test_one_recommendation_per_customer_with_required_keys():
    out = cr.recommend_for_customers([_c("a"), _c("b")], [])
    assert len(out) == 2
    for row in out:
        assert {"customer_id", "segment", "priorite", "action", "playbook", "raison"} <= set(row)


def test_abandoned_cart_overrides_segment_action():
    out = cr.recommend_for_customers([_c("a")], [_o("a", "abandoned")])
    assert out[0]["action"] == "Relance de panier abandonné (prioritaire)"
    assert out[0]["priorite"] == "Élevée" and out[0]["playbook"] == "Abandoned Cart Recovery"


def test_high_churn_score_triggers_urgent_retention():
    out = cr.recommend_for_customers([_c("a", churn_risk_score=0.7)], [])
    assert out[0]["action"] == "Rétention urgente (score de churn élevé)"
    assert out[0]["playbook"] == "Churn Reduction" and "0.70" in out[0]["raison"]


def test_churn_score_just_below_threshold_does_not_override():
    out = cr.recommend_for_customers([_c("a", churn_risk_score=0.69)], [])
    assert out[0]["action"] != "Rétention urgente (score de churn élevé)"


def test_abandoned_cart_wins_over_high_churn():
    out = cr.recommend_for_customers([_c("a", churn_risk_score=0.95)], [_o("a", "abandoned")])
    assert out[0]["playbook"] == "Abandoned Cart Recovery"


def test_invalid_churn_value_is_ignored():
    out = cr.recommend_for_customers([_c("a", churn_risk_score="n/a")], [])
    assert out[0]["action"] != "Rétention urgente (score de churn élevé)"


def test_results_sorted_high_priority_first_then_by_customer_id():
    customers = [_c("z", churn_risk_score=0.9), _c("a"), _c("m", churn_risk_score=0.8)]
    out = cr.recommend_for_customers(customers, [])
    prios = [r["priorite"] for r in out]
    assert prios == sorted(prios, key=lambda p: {"Élevée": 0, "Moyenne": 1}[p])
    assert [r["customer_id"] for r in out if r["priorite"] == "Élevée"] == ["m", "z"]


def test_strategic_note_is_appended_for_matching_segment():
    base = cr.recommend_for_customers([_c("a")], [])[0]
    seg = base["segment"]
    out = cr.recommend_for_customers([_c("a")], [], strategic_notes={seg: "NOTE-LLM"})[0]
    assert out["raison"].endswith("Stratégie segment : NOTE-LLM")


def test_customer_with_unmatched_orders_still_gets_a_recommendation():
    out = cr.recommend_for_customers([_c("a")], [_o("someone_else")])
    assert out[0]["customer_id"] == "a"


# ---------------------- build_strategic_notes_from_analysis ------------------
def test_notes_from_analysis_keyword_matching_and_truncation():
    result = {"recommendations": [
        {"title": "Réduire le churn", "summary": "", "justification": ""},
        {"title": "Campagne de bienvenue", "summary": "x" * 500, "justification": ""},
    ]}
    notes = cr.build_strategic_notes_from_analysis(result)
    assert notes["At Risk"] == "Réduire le churn"
    assert notes["New / Promising"] == "Campagne de bienvenue"


def test_notes_first_recommendation_wins_per_segment():
    result = {"recommendations": [{"title": "Churn A"}, {"title": "Churn B"}]}
    assert cr.build_strategic_notes_from_analysis(result)["At Risk"] == "Churn A"


@pytest.mark.parametrize("result", [{}, {"recommendations": None}, {"recommendations": []}])
def test_notes_empty_inputs(result):
    assert cr.build_strategic_notes_from_analysis(result) == {}


def test_notes_title_is_truncated_to_180_chars():
    notes = cr.build_strategic_notes_from_analysis({"recommendations": [{"title": "churn " + "x" * 400}]})
    assert len(notes["At Risk"]) == 180

"""Integration: Decision Engine pipeline over a seeded temp DB.
Understand -> Observe -> Detect -> Retrieve(Chroma) -> Reason -> Plan -> Decide -> Recommend.
Only the LLM (scripted fake) and the embedder (hash fake) are replaced."""
import json
from pathlib import Path

import pytest

from core.models import AnalysisRequest, DecisionState, RecommendationStatus
from engine.decision_engine import DecisionEngine
from engine.nodes import understand_node, observe_node, detect_node, retrieve_node
from knowledge.loader import load_playbooks
from helpers_eleva import seed_company, EXPECTED_KPIS, SYNTHETIC_PROFILE

def _req(company="co_test", n=3, q="Que faire ?"):
    return AnalysisRequest(company_id=company, question=q, max_recommendations=n)


def _run(company="co_test", n=3):
    return DecisionEngine().run(_req(company, n))


# ------------------------------- step by step --------------------------------
def test_understand_loads_profile_from_db(seeded_company):
    st = understand_node(DecisionState(request=_req()))
    assert st.errors == [] and st.company_context.name == SYNTHETIC_PROFILE["name"] and st.current_step == "observe"


def test_understand_unknown_company_records_error():
    st = understand_node(DecisionState(request=_req("ghost")))
    assert st.company_context is None and "Profile not found" in st.errors[0]


def test_observe_kpis_match_hand_computed_values(seeded_company):
    st = observe_node(DecisionState(request=_req()))
    got = {k.name: k.value for k in st.observation.kpis}
    for name in ("total_customers", "total_orders", "completed_orders", "abandoned_orders",
                 "cart_abandonment_rate", "average_order_value", "repeat_purchase_rate",
                 "approx_clv", "high_churn_risk_count"):
        assert got[name] == EXPECTED_KPIS[name], name
    assert st.current_step == "detect"


def test_observe_segments_cover_every_customer_and_sum_to_100_percent(seeded_company):
    obs = observe_node(DecisionState(request=_req())).observation
    assert sum(s.size for s in obs.segments) == 8
    assert abs(sum(s.percentage for s in obs.segments) - 100) < 0.5


def test_observe_insights_mention_abandonment_churn_and_low_roi(seeded_company):
    text = " ".join(observe_node(DecisionState(request=_req())).observation.raw_insights)
    assert "2 panier(s) abandonné(s)" in text and "25%" in text
    assert "2 client(s) avec un score de churn élevé" in text
    assert "Camp B" in text


def test_detect_after_observe_finds_expected_issues(seeded_company):
    st = detect_node(observe_node(DecisionState(request=_req())))
    titles = {i.title for i in st.detected_issues}
    assert "Taux d'abandon de panier élevé" in titles          # 0.25 >= 0.25
    assert "Scores de risque de churn élevés" in titles
    assert "Taux de réachat faible" not in titles              # repeat rate = 1.0


# @pytest.mark.xfail(strict=True, reason="BUG-1 (end-to-end): Camp B has ROI 1.0 (<1.5) and observe reports it, but detect never turns it into an issue")
def test_low_roi_campaign_becomes_a_detected_issue_end_to_end(seeded_company):
    st = detect_node(observe_node(DecisionState(request=_req())))
    assert "Campagnes sous-performantes" in {i.title for i in st.detected_issues}


def test_retrieve_passes_real_playbooks_linked_to_real_issues(seeded_company):
    st = detect_node(observe_node(DecisionState(request=_req())))
    st = retrieve_node(st)
    issue_ids = {i.id for i in st.detected_issues}
    assert st.retrieved_playbooks and st.current_step == "reason"
    techniques = [p["technique"] for p in st.retrieved_playbooks]
    assert len(techniques) == len(set(techniques))             # de-duplicated
    assert set(techniques) <= {p["Technique"] for p in load_playbooks()}
    assert all(p["issue_id"] in issue_ids and p["content"] for p in st.retrieved_playbooks)


def test_retrieve_with_no_issues_skips_without_touching_chroma(tmp_path):
    from config import settings
    st = retrieve_node(DecisionState(request=_req()))
    assert st.retrieved_playbooks == [] and st.current_step == "reason"
    assert not Path(settings.chroma_persist_dir).exists()


# ------------------------------- full pipeline -------------------------------
def test_full_run_with_scripted_llm_completes(seeded_company, fake_llm):
    st = _run()
    assert st.errors == [] and st.current_step == "done"
    assert st.company_context and st.observation and st.detected_issues and st.retrieved_playbooks
    assert 1 <= len(st.recommendations) <= 3
    assert {r.status for r in st.recommendations} == {RecommendationStatus.PENDING_APPROVAL}
    assert all(r.company_id == "co_test" for r in st.recommendations)


def test_llm_is_called_once_per_stage_in_order(seeded_company, fake_llm):
    _run()
    assert [c["stage"] for c in fake_llm.calls] == ["reason", "plan", "recommend"]


def test_context_flows_from_detection_and_retrieval_into_the_llm_prompts(seeded_company, fake_llm):
    st = _run()
    reason_prompt = fake_llm.calls_for("reason")[0]["user"]
    for issue in st.detected_issues:
        assert issue.title in reason_prompt
    for pb in st.retrieved_playbooks:
        assert pb["technique"] in reason_prompt
    assert SYNTHETIC_PROFILE["name"] in reason_prompt and "Que faire ?" in reason_prompt
    plan_prompt = fake_llm.calls_for("plan")[0]["user"]
    assert all(h.statement in plan_prompt for h in st.hypotheses)
    rec_prompt = fake_llm.calls_for("recommend")[0]["user"]
    assert "Strategie 1" in rec_prompt or "Strategie 2" in rec_prompt


def test_max_recommendations_is_respected_end_to_end(seeded_company, fake_llm):
    assert len(_run(n=1).recommendations) == 1


def test_unknown_company_stops_at_understand_and_never_calls_llm(fake_llm):
    st = _run("ghost")
    assert st.errors and st.current_step == "understand" and st.observation is None
    assert st.recommendations == [] and fake_llm.calls == []


def test_llm_outage_degrades_gracefully_to_fallback_recommendations(seeded_company, llm_down):
    st = _run()
    assert st.errors == [] and st.current_step == "done" and st.recommendations
    assert all("fallback" in r.justification.lower() for r in st.recommendations)
    assert {r.status for r in st.recommendations} == {RecommendationStatus.PENDING_APPROVAL}


def test_malformed_llm_output_at_every_stage_still_gives_recommendations(seeded_company, fake_llm):
    for stage in ("reason", "plan", "recommend"):
        fake_llm.set(stage, "Je ne suis pas du JSON")
    assert _run().recommendations


def test_llm_failing_only_at_plan_stage_still_completes(seeded_company, fake_llm):
    fake_llm.set("plan", TimeoutError("slow"))
    assert _run().current_step == "done"


def test_company_with_profile_but_no_data_runs_without_crashing(fake_llm):
    seed_company("empty_co", customers=[], orders=[], campaigns=[])
    st = _run("empty_co")
    assert st.errors == [] and st.current_step == "done"


def test_LIMITATION_empty_company_is_reported_as_having_a_low_repeat_rate(fake_llm):
    """LIMITATION-4 (characterisation): with 0 customers/orders, repeat rate is 0.0, which is
    < 30 %, so Eleva reports 'Taux de réachat faible' about a company with no data at all."""
    seed_company("empty_co", customers=[], orders=[], campaigns=[])
    assert "Taux de réachat faible" in {i.title for i in _run("empty_co").detected_issues}


def test_multi_tenant_isolation_in_observation_and_prompts(fake_llm):
    seed_company("A")
    seed_company("B", profile={"name": "Company B Only", "industry": "food"},
                 customers=[{"customer_id": "b1", "total_orders": 1, "total_spent": 5.0}], orders=[], campaigns=[])
    st = _run("B")
    got = {k.name: k.value for k in st.observation.kpis}
    assert got["total_customers"] == 1 and got["total_orders"] == 0
    prompts = " ".join(c["user"] for c in fake_llm.calls)
    assert "Company B Only" in prompts and SYNTHETIC_PROFILE["name"] not in prompts

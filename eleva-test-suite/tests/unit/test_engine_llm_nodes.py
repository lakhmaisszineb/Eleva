"""Unit tests: engine/nodes/reason.py, plan.py, recommend.py with a CONTROLLED fake LLM.

These prove how Eleva handles good / malformed / failing LLM output. They do NOT
prove that the real Groq model produces good advice (see tests/live/)."""
import json

import pytest

from core.models import (AnalysisRequest, DecisionState, CompanyContext, DetectedIssue,
                         Hypothesis, Strategy, IssueType, Priority, RecommendationStatus)
from engine.nodes.reason import reason_node, _extract_json
from engine.nodes.plan import plan_node
from engine.nodes.recommend import recommend_node


def _state(n_issues=2, max_reco=3):
    st = DecisionState(request=AnalysisRequest(company_id="c", question="Que faire ?", max_recommendations=max_reco))
    st.company_context = CompanyContext(company_id="c", name="Acme", industry="beauty", goals=["g1", "g2"])
    st.detected_issues = [
        DetectedIssue(id=f"i{n}", type=IssueType.PROBLEM, title=f"Issue {n}", description="desc",
                      priority=Priority.HIGH, evidence=[f"ev{n}"]) for n in range(n_issues)
    ]
    st.retrieved_playbooks = [{"issue_id": "i0", "issue_title": "Issue 0", "technique": "Win-back", "content": "x", "distance": 0.1}]
    return st


# ================================ REASON =====================================
def test_extract_json_handles_fences():
    assert _extract_json('```json\n{"hypotheses": []}\n```') == {"hypotheses": []}


def test_reason_valid_llm_response_links_hypotheses_to_matching_issue(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": [
        {"issue_title": "Issue 1", "statement": "S1", "confidence": 0.9}]}))
    st = reason_node(_state())
    (h,) = st.hypotheses
    assert h.statement == "S1" and h.confidence == 0.9 and h.related_issue_ids == ["i1"]
    assert st.current_step == "plan"


def test_reason_prompt_receives_context_issues_and_playbooks(fake_llm):
    reason_node(_state())
    user = fake_llm.calls_for("reason")[0]["user"]
    for expected in ("Acme", "beauty", "g1, g2", "Issue 0", "Issue 1", "Win-back", "Que faire ?"):
        assert expected in user


@pytest.mark.parametrize("bad", ["Désolé, je ne peux pas.", "", "{truncated json", "[]"])
def test_reason_malformed_output_uses_deterministic_fallback(fake_llm, bad):
    fake_llm.set("reason", bad)
    st = reason_node(_state())
    assert len(st.hypotheses) == 2                       # one per issue
    assert all(h.confidence == 0.6 for h in st.hypotheses)
    assert st.hypotheses[0].supporting_evidence == ["ev0"]
    assert "Win-back" in st.hypotheses[0].statement      # playbook of issue i0 is used


@pytest.mark.parametrize("exc", [TimeoutError("t"), ConnectionError("c"), ValueError("GROQ_API_KEY missing")])
def test_reason_api_errors_use_fallback(fake_llm, exc):
    fake_llm.set("reason", exc)
    st = reason_node(_state())
    assert len(st.hypotheses) == 2 and st.errors == []   # degraded, not failed


def test_reason_out_of_range_confidence_discards_llm_output_and_falls_back(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": [
        {"issue_title": "Issue 0", "statement": "ok", "confidence": 1.7}]}))
    st = reason_node(_state())
    assert all(h.confidence == 0.6 for h in st.hypotheses)   # pydantic rejected 1.7 -> fallback


def test_reason_unmatched_issue_title_links_to_first_issue(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": [
        {"issue_title": "totally unrelated", "statement": "S", "confidence": 0.5}]}))
    assert reason_node(_state()).hypotheses[0].related_issue_ids == ["i0"]


def test_reason_no_issues_and_no_hypotheses(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": []}))
    st = reason_node(_state(n_issues=0))
    assert st.hypotheses == [] and st.current_step == "plan"


@pytest.mark.xfail(strict=True, reason="BUG-4: a hypothesis with no 'issue_title' matches EVERY issue ('' is a substring of any title)")
def test_reason_missing_issue_title_should_not_link_to_all_issues(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": [{"statement": "S", "confidence": 0.5}]}))
    assert len(reason_node(_state(n_issues=3)).hypotheses[0].related_issue_ids) == 1


@pytest.mark.xfail(strict=True, reason="BUG-6: one null field ('confidence': null) throws away the whole LLM answer")
def test_reason_null_confidence_keeps_valid_llm_text(fake_llm):
    fake_llm.set("reason", json.dumps({"hypotheses": [
        {"issue_title": "Issue 0", "statement": "KEEP-ME", "confidence": None}]}))
    assert reason_node(_state()).hypotheses[0].statement == "KEEP-ME"


# ================================= PLAN ======================================
def _planned():
    st = _state()
    st.hypotheses = [Hypothesis(id="h0", statement="H0", confidence=0.7, related_issue_ids=["i0"]),
                     Hypothesis(id="h1", statement="H1", confidence=0.7, related_issue_ids=["i1"])]
    return st


def test_plan_valid_llm_response(fake_llm):
    st = plan_node(_planned())
    assert [s.name for s in st.strategies] == ["Strategie 1", "Strategie 2"]
    assert st.strategies[0].recommended_playbooks == ["Win-back / Reactivation Campaign"]
    assert st.strategies[0].risks == ["risque"] and st.current_step == "decide"


def test_plan_missing_fields_get_defaults(fake_llm):
    fake_llm.set("plan", json.dumps({"strategies": [{}]}))
    (s,) = plan_node(_planned()).strategies
    assert s.name == "Stratégie" and s.description == "" and s.recommended_playbooks == []


@pytest.mark.parametrize("bad", ["nope", "", "{oops"])
def test_plan_malformed_output_builds_one_fallback_strategy_per_hypothesis(fake_llm, bad):
    fake_llm.set("plan", bad)
    st = plan_node(_planned())
    assert len(st.strategies) == 2
    assert [s.related_hypothesis_ids for s in st.strategies] == [["h0"], ["h1"]]
    assert st.strategies[0].description == "H0"


def test_plan_llm_exception_uses_fallback(fake_llm):
    fake_llm.set("plan", TimeoutError("slow"))
    assert len(plan_node(_planned()).strategies) == 2


def test_plan_prompt_contains_hypotheses_and_playbooks(fake_llm):
    plan_node(_planned())
    user = fake_llm.calls_for("plan")[0]["user"]
    assert "H0" in user and "H1" in user and "Win-back" in user


def test_plan_LIMITATION_every_llm_strategy_is_linked_only_to_the_first_hypothesis(fake_llm):
    """LIMITATION-2 (characterisation): plan_node links ALL LLM strategies to hypotheses[0].
    Consequence: decide_node's priority filter effectively looks at one issue only."""
    st = plan_node(_planned())
    assert all(s.related_hypothesis_ids == ["h0"] for s in st.strategies)


# ================================ RECOMMEND ==================================
def _with_strategies(max_reco=3):
    st = _state(max_reco=max_reco)
    st.strategies = [Strategy(id="s0", name="S0", description="D0", recommended_playbooks=["P"]),
                     Strategy(id="s1", name="S1", description="D1")]
    return st


def test_recommend_valid_llm_response(fake_llm):
    st = recommend_node(_with_strategies())
    assert [r.title for r in st.recommendations] == ["Reco 1", "Reco 2"]
    assert st.recommendations[0].priority == Priority.HIGH
    assert st.recommendations[0].expected_outcomes == ["o1"] and st.current_step == "done"
    assert all(r.company_id == "c" for r in st.recommendations)


def test_recommend_always_requires_human_approval(fake_llm):
    st = recommend_node(_with_strategies())
    assert {r.status for r in st.recommendations} == {RecommendationStatus.PENDING_APPROVAL}


def test_recommend_truncates_to_max_recommendations(fake_llm):
    assert len(recommend_node(_with_strategies(max_reco=1)).recommendations) == 1


@pytest.mark.parametrize("label,expected", [("HIGH", Priority.HIGH), ("critical", Priority.CRITICAL),
                                            ("low", Priority.LOW), ("urgentissime", Priority.MEDIUM)])
def test_recommend_priority_mapping_is_case_insensitive_with_medium_default(fake_llm, label, expected):
    fake_llm.set("recommend", json.dumps({"recommendations": [{"title": "t", "priority": label}]}))
    assert recommend_node(_with_strategies()).recommendations[0].priority == expected


@pytest.mark.parametrize("bad", ["texte libre", "", "{", "null"])
def test_recommend_malformed_output_uses_fallback_from_strategies(fake_llm, bad):
    fake_llm.set("recommend", bad)
    st = recommend_node(_with_strategies())
    assert [r.title for r in st.recommendations] == ["S0", "S1"]
    assert "fallback" in st.recommendations[0].justification.lower()
    assert st.recommendations[0].status == RecommendationStatus.PENDING_APPROVAL


def test_recommend_llm_down_fallback_respects_max_recommendations(llm_down):
    st = recommend_node(_with_strategies(max_reco=1))
    assert [r.title for r in st.recommendations] == ["S0"]


def test_recommend_llm_down_and_no_strategies_gives_no_recommendations(llm_down):
    st = _state()
    assert recommend_node(st).recommendations == []


def test_recommend_prompt_includes_strategies_and_limit(fake_llm):
    recommend_node(_with_strategies(max_reco=2))
    user = fake_llm.calls_for("recommend")[0]["user"]
    assert "S0" in user and "D1" in user and "Acme" in user and "2" in user


def test_recommend_LIMITATION_every_llm_recommendation_gets_the_same_first_strategy(fake_llm):
    """LIMITATION-3 (characterisation): strategies=state.strategies[:1] for every recommendation."""
    st = recommend_node(_with_strategies())
    assert all([s.id for s in r.strategies] == ["s0"] for r in st.recommendations)


@pytest.mark.xfail(strict=True, reason="BUG-6: 'priority': null makes .lower() raise -> whole LLM answer discarded")
def test_recommend_null_priority_keeps_valid_llm_text(fake_llm):
    fake_llm.set("recommend", json.dumps({"recommendations": [{"title": "KEEP-ME", "priority": None}]}))
    assert recommend_node(_with_strategies()).recommendations[0].title == "KEEP-ME"

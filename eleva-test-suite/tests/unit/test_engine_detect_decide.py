"""Unit tests: engine/nodes/detect.py and decide.py (deterministic business rules, no LLM)."""
import pytest

from core.models import (AnalysisRequest, DecisionState, Observation, KPI, SegmentSummary,
                         DetectedIssue, Hypothesis, Strategy, IssueType, Priority)
from engine.nodes.detect import detect_node
from engine.nodes.decide import decide_node


def _state(kpis=None, segments=None, insights=None, with_obs=True):
    st = DecisionState(request=AnalysisRequest(company_id="c", question="q"))
    if with_obs:
        st.observation = Observation(
            company_id="c",
            kpis=[KPI(name=k, value=v) for k, v in (kpis or {}).items()],
            segments=[SegmentSummary(name=n, size=s, percentage=p) for n, s, p in (segments or [])],
            raw_insights=insights or [],
        )
    return st


def _titles(st):
    return [i.title for i in st.detected_issues]


# --------------------------------- detect ------------------------------------
def test_detect_without_observation_records_error_and_does_not_advance():
    st = detect_node(_state(with_obs=False))
    assert st.errors == ["Detect failed: no observation available"]
    assert st.detected_issues == [] and st.current_step == "understand"


def test_detect_healthy_company_has_no_issues():
    st = detect_node(_state(kpis={"cart_abandonment_rate": 0.1, "high_churn_risk_count": 0, "repeat_purchase_rate": 0.8}))
    assert st.detected_issues == [] and st.current_step == "retrieve"


@pytest.mark.parametrize("rate,fires", [(0.24, False), (0.25, True), (0.9, True)])
def test_detect_abandonment_threshold_inclusive_at_25_percent(rate, fires):
    st = detect_node(_state(kpis={"cart_abandonment_rate": rate, "abandoned_orders": 3}))
    assert ("Taux d'abandon de panier élevé" in _titles(st)) is fires


@pytest.mark.parametrize("rate,fires", [(0.29, True), (0.30, False)])
def test_detect_low_repeat_rate_threshold_exclusive_at_30_percent(rate, fires):
    st = detect_node(_state(kpis={"repeat_purchase_rate": rate}))
    assert ("Taux de réachat faible" in _titles(st)) is fires


@pytest.mark.parametrize("count,fires", [(0, False), (1, True)])
def test_detect_high_churn_count(count, fires):
    st = detect_node(_state(kpis={"high_churn_risk_count": count}))
    assert ("Scores de risque de churn élevés" in _titles(st)) is fires


@pytest.mark.parametrize("pct,prio", [(14.9, Priority.MEDIUM), (15.0, Priority.HIGH), (40, Priority.HIGH)])
def test_detect_at_risk_priority_boundary_at_15_percent(pct, prio):
    st = detect_node(_state(segments=[("At Risk", 3, pct)]))
    (issue,) = st.detected_issues
    assert issue.type == IssueType.PROBLEM and issue.priority == prio


def test_detect_segment_of_size_zero_is_ignored():
    assert detect_node(_state(segments=[("At Risk", 0, 0.0), ("Champions", 0, 0.0)])).detected_issues == []


def test_detect_opportunities_are_typed_correctly():
    st = detect_node(_state(segments=[("Champions", 2, 20.0), ("New / Promising", 1, 10.0)]))
    assert {i.type for i in st.detected_issues} == {IssueType.OPPORTUNITY}
    assert len(st.detected_issues) == 2


def test_detect_issue_ids_are_unique_and_evidence_present():
    st = detect_node(_state(kpis={"cart_abandonment_rate": 0.5, "abandoned_orders": 5, "high_churn_risk_count": 2},
                            segments=[("At Risk", 2, 20.0), ("Lost / Churned", 1, 10.0)]))
    ids = [i.id for i in st.detected_issues]
    assert len(ids) == len(set(ids)) == 4
    assert all(i.evidence for i in st.detected_issues)


@pytest.mark.xfail(strict=True, reason="BUG-1: detect.py lowercases the insight then searches for 'faible ROI' (uppercase ROI) -> never matches, so low-ROI campaigns are never reported as an issue")
def test_detect_low_roi_issue_from_the_exact_insight_text_produced_by_observe():
    """observe_node writes: 'Campagnes à faible ROI détectées : <names>.'
    detect_node must turn that into a 'Campagnes sous-performantes' issue."""
    insight = "Campagnes à faible ROI détectées : Camp B."
    st = detect_node(_state(insights=[insight]))
    assert "Campagnes sous-performantes" in _titles(st)


# --------------------------------- decide ------------------------------------
def _issue(i, prio):
    return DetectedIssue(id=i, type=IssueType.PROBLEM, title=i, description="d", priority=prio)


def _decide_state(issue_prios, link_every_strategy_to_issue=True):
    st = DecisionState(request=AnalysisRequest(company_id="c", question="q"))
    st.detected_issues = [_issue(f"i{n}", p) for n, p in enumerate(issue_prios)]
    for n, _ in enumerate(issue_prios):
        st.hypotheses.append(Hypothesis(id=f"h{n}", statement="s", confidence=0.5, related_issue_ids=[f"i{n}"]))
        st.strategies.append(Strategy(id=f"s{n}", name=f"S{n}", description="d", related_hypothesis_ids=[f"h{n}"]))
    return st


def test_decide_keeps_strategies_of_the_three_highest_priority_issues():
    st = _decide_state([Priority.LOW, Priority.MEDIUM, Priority.CRITICAL, Priority.HIGH, Priority.LOW])
    out = decide_node(st)
    # top-3 by priority: i2 (critical), i3 (high), i1 (medium)
    assert sorted(s.id for s in out.strategies) == ["s1", "s2", "s3"]
    assert out.current_step == "recommend"


def test_decide_tie_break_is_stable_original_order():
    st = _decide_state([Priority.HIGH, Priority.HIGH, Priority.HIGH, Priority.HIGH])
    assert sorted(s.id for s in decide_node(st).strategies) == ["s0", "s1", "s2"]


def test_decide_falls_back_to_first_three_when_nothing_is_linked():
    st = _decide_state([Priority.LOW] * 5)
    for s in st.strategies:
        s.related_hypothesis_ids = ["unknown"]
    assert [s.id for s in decide_node(st).strategies] == ["s0", "s1", "s2"]


def test_decide_with_no_strategies_is_safe():
    st = DecisionState(request=AnalysisRequest(company_id="c", question="q"))
    assert decide_node(st).strategies == []

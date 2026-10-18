"""
Tests unitaires pour engine/nodes/detect.py
"""
from engine.nodes.detect import detect_node
from core.models import (
    DecisionState,
    AnalysisRequest,
    Observation,
    KPI,
    SegmentSummary,
)


def _make_state(**kwargs):
    """Helper : crée un DecisionState minimal."""
    state = DecisionState(
        request=AnalysisRequest(company_id="test", question="test")
    )
    for key, value in kwargs.items():
        setattr(state, key, value)
    return state


class TestDetectNodeErrors:
    """Tests de gestion d'erreur."""

    def test_no_observation(self):
        """Sans observation → erreur."""
        state = _make_state()
        state = detect_node(state)
        assert len(state.errors) > 0
        assert "no observation" in state.errors[0].lower()


class TestDetectProblems:
    """Tests de détection de problèmes."""

    def test_high_abandonment_rate(self):
        """Taux d'abandon ≥ 25% → problème HIGH."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            kpis=[KPI(name="cart_abandonment_rate", value=0.30)],
        )
        state = detect_node(state)
        abandon_issues = [i for i in state.detected_issues if "abandon" in i.title.lower()]
        assert len(abandon_issues) == 1
        assert abandon_issues[0].priority.value == "high"

    def test_low_abandonment_rate_no_issue(self):
        """Taux d'abandon < 25% → pas de problème."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            kpis=[KPI(name="cart_abandonment_rate", value=0.10)],
        )
        state = detect_node(state)
        abandon_issues = [i for i in state.detected_issues if "abandon" in i.title.lower()]
        assert len(abandon_issues) == 0

    def test_at_risk_segment(self):
        """Segment 'At Risk' → problème."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            segments=[
                SegmentSummary(name="At Risk", size=10, percentage=15.0, key_metrics={}),
            ],
        )
        state = detect_node(state)
        at_risk_issues = [i for i in state.detected_issues if "churn" in i.title.lower()]
        assert len(at_risk_issues) == 1

    def test_high_churn_risk(self):
        """high_churn_risk_count > 0 → problème HIGH."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            kpis=[KPI(name="high_churn_risk_count", value=5)],
        )
        state = detect_node(state)
        churn_issues = [i for i in state.detected_issues if "churn" in i.title.lower()]
        assert len(churn_issues) == 1
        assert churn_issues[0].priority.value == "high"

    def test_low_repeat_purchase_rate(self):
        """Taux de réachat < 30% → problème."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            kpis=[KPI(name="repeat_purchase_rate", value=0.20)],
        )
        state = detect_node(state)
        repeat_issues = [i for i in state.detected_issues if "réachat" in i.title.lower()]
        assert len(repeat_issues) == 1


class TestDetectOpportunities:
    """Tests de détection d'opportunités."""

    def test_champions_segment(self):
        """Segment 'Champions' → opportunité."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            segments=[
                SegmentSummary(name="Champions", size=5, percentage=8.0, key_metrics={}),
            ],
        )
        state = detect_node(state)
        opps = [i for i in state.detected_issues if i.type.value == "opportunity"]
        assert len(opps) == 1
        assert "Champions" in opps[0].title

    def test_new_promising_segment(self):
        """Segment 'New / Promising' → opportunité."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            segments=[
                SegmentSummary(name="New / Promising", size=3, percentage=5.0, key_metrics={}),
            ],
        )
        state = detect_node(state)
        opps = [i for i in state.detected_issues if i.type.value == "opportunity"]
        assert len(opps) == 1


class TestDetectStateUpdates:
    """Tests de mise à jour de l'état."""

    def test_current_step_updated(self):
        """current_step passe à 'retrieve'."""
        state = _make_state()
        state.observation = Observation(company_id="test", kpis=[], segments=[])
        state = detect_node(state)
        assert state.current_step == "retrieve"

    def test_issues_stored_in_state(self):
        """Les problèmes sont stockés dans state.detected_issues."""
        state = _make_state()
        state.observation = Observation(
            company_id="test",
            kpis=[KPI(name="cart_abandonment_rate", value=0.30)],
        )
        state = detect_node(state)
        assert len(state.detected_issues) > 0
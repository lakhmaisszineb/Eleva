"""Unit tests: engine/explain.py and llm/groq_client.py."""
import pytest

from core.models import (AnalysisRequest, DecisionState, CompanyContext, Observation, KPI, SegmentSummary,
                         DetectedIssue, Hypothesis, Recommendation, Strategy, IssueType, Priority)
from engine.explain import explain_recommendation, format_explanation_for_display
import llm.groq_client as gc


# ================================ EXPLAIN ====================================
def _full_state():
    st = DecisionState(request=AnalysisRequest(company_id="c", question="Pourquoi ?"))
    st.company_context = CompanyContext(company_id="c", name="Acme", industry="beauty", current_focus="retention", goals=["g"])
    st.observation = Observation(company_id="c", kpis=[KPI(name="aov", value=75.0, unit="currency")],
                                 segments=[SegmentSummary(name="At Risk", size=2, percentage=25.0)],
                                 raw_insights=["insight-1"])
    st.detected_issues = [DetectedIssue(id="i1", type=IssueType.PROBLEM, title="Gros problème", description="d",
                                        priority=Priority.HIGH, evidence=["e1"])]
    st.retrieved_playbooks = [{"technique": "Win-back", "issue_title": "Gros problème"}]
    st.hypotheses = [Hypothesis(id="h1", statement="Hyp", confidence=0.5)]
    strat = Strategy(id="s1", name="Strat", description="sd", recommended_playbooks=["Win-back"])
    st.recommendations = [
        Recommendation(id="r1", company_id="c", title="Reco A", summary="sa", justification="ja", strategies=[strat],
                       next_steps=["step"]),
        Recommendation(id="r2", company_id="c", title="Reco B", summary="sb", justification="jb"),
    ]
    return st


def test_explain_without_recommendations_returns_error_dict():
    st = DecisionState(request=AnalysisRequest(company_id="c", question="q"))
    out = explain_recommendation(st)
    assert out["recommendation_id"] is None and "Aucune recommandation" in out["error"]


def test_explain_defaults_to_first_recommendation():
    assert explain_recommendation(_full_state())["recommendation_id"] == "r1"


def test_explain_by_id_and_unknown_id_falls_back_to_first():
    st = _full_state()
    assert explain_recommendation(st, "r2")["recommendation_title"] == "Reco B"
    assert explain_recommendation(st, "does-not-exist")["recommendation_id"] == "r1"


def test_explain_contains_signals_issues_playbooks_hypotheses():
    out = explain_recommendation(_full_state())
    assert "KPI aov = 75.0 currency" in out["signals"]
    assert "Insight: insight-1" in out["signals"]
    assert any("At Risk" in s and "25.0%" in s for s in out["signals"])
    assert out["detected_issues"][0]["evidence"] == ["e1"]
    assert out["playbooks_used"] == [{"technique": "Win-back", "for_issue": "Gros problème"}]
    assert out["hypotheses"] == ["Hyp"] and out["strategies"][0]["name"] == "Strat"


def test_explain_narrative_states_human_approval_and_high_priority_issue():
    n = explain_recommendation(_full_state())["narrative"]
    assert "pending_approval" in n and "validation humaine" in n
    assert "Gros problème" in n and "Win-back" in n and "ja" in n


def test_explain_works_with_minimal_state():
    st = DecisionState(request=AnalysisRequest(company_id="c", question="q"))
    st.recommendations = [Recommendation(id="r", company_id="c", title="T", summary="s", justification="j")]
    out = explain_recommendation(st)
    assert out["company"] == {} and out["signals"] == [] and "T" in out["narrative"]


def test_format_explanation_for_display_sections():
    text = format_explanation_for_display(explain_recommendation(_full_state()))
    for needle in ("EXPLICATION DE LA RECOMMANDATION", "Reco A", "preuve: e1", "Win-back", "→ step", "Note RGPD"):
        assert needle in text


def test_format_explanation_error_passthrough():
    assert format_explanation_for_display({"error": "boom"}) == "boom"


# =============================== GROQ CLIENT =================================
class _FakeChatGroq:
    last = None

    def __init__(self, **kw):
        self.kw = kw
        self.messages = None
        _FakeChatGroq.last = self

    def invoke(self, messages):
        self.messages = messages

        class R:
            content = "  réponse  \n"
        return R()


@pytest.fixture
def fake_groq(monkeypatch):
    from config import settings
    monkeypatch.setattr(gc, "ChatGroq", _FakeChatGroq)
    monkeypatch.setattr(settings, "groq_api_key", "gsk_real_looking_key")
    return _FakeChatGroq


@pytest.mark.parametrize("key", ["", "your_groq_api_key_here"])
def test_get_llm_rejects_missing_or_placeholder_key(monkeypatch, key):
    from config import settings
    monkeypatch.setattr(settings, "groq_api_key", key)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        gc.get_llm()


def test_get_llm_uses_settings_and_is_a_singleton(fake_groq):
    a, b = gc.get_llm(), gc.get_llm()
    assert a is b
    assert a.kw["api_key"] == "gsk_real_looking_key" and a.kw["temperature"] == 0.3 and a.kw["max_tokens"] == 2048
    assert a.kw["model"] == "openai/gpt-oss-120b"


def test_chat_builds_messages_and_strips_output(fake_groq):
    out = gc.chat("SYS", "USER", history=[{"role": "user", "content": "u1"}, {"role": "assistant", "content": "a1"},
                                            {"role": "system", "content": "ignored"}])
    assert out == "réponse"
    kinds = [type(m).__name__ for m in fake_groq.last.messages]
    assert kinds == ["SystemMessage", "HumanMessage", "AIMessage", "HumanMessage"]
    assert fake_groq.last.messages[-1].content == "USER"


def test_chat_without_history(fake_groq):
    gc.chat("SYS", "USER")
    assert [type(m).__name__ for m in fake_groq.last.messages] == ["SystemMessage", "HumanMessage"]


def test_chat_propagates_api_errors(fake_groq, monkeypatch):
    monkeypatch.setattr(_FakeChatGroq, "invoke", lambda self, m: (_ for _ in ()).throw(TimeoutError("slow")))
    with pytest.raises(TimeoutError):
        gc.chat("s", "u")

"""Unit tests: config/settings.py, core/models.py, core/exceptions.py."""
import pytest
from pydantic import ValidationError

from config.settings import Settings
from core import models as m
from core.exceptions import (ElevaError, DataNotFoundError, InvalidCompanyError,
                             ObservationError, ReasoningError)


# --------------------------------- settings ----------------------------------
def test_settings_requires_groq_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_defaults_and_helpers(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    for var in ("APP_ENV", "LOG_LEVEL", "DEFAULT_COMPANY_ID", "GROQ_MODEL"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.groq_model == "openai/gpt-oss-120b" and s.log_level == "INFO"
    assert s.default_company_id == "company_001"
    assert s.is_development and not s.is_production


def test_settings_env_override_and_case_insensitive(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("app_env", "PRODUCTION")
    s = Settings(_env_file=None)
    assert s.is_production and not s.is_development


def test_settings_ignores_unknown_env_vars(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("TOTALLY_UNKNOWN", "x")
    Settings(_env_file=None)   # must not raise (extra="ignore")


# ----------------------------------- models ----------------------------------
@pytest.mark.parametrize("n", [0, 11, -1])
def test_analysis_request_max_recommendations_bounds(n):
    with pytest.raises(ValidationError):
        m.AnalysisRequest(company_id="c", question="q", max_recommendations=n)


@pytest.mark.parametrize("n", [1, 3, 10])
def test_analysis_request_max_recommendations_valid(n):
    assert m.AnalysisRequest(company_id="c", question="q", max_recommendations=n).max_recommendations == n


def test_analysis_request_requires_company_and_question():
    with pytest.raises(ValidationError):
        m.AnalysisRequest(question="q")
    with pytest.raises(ValidationError):
        m.AnalysisRequest(company_id="c")


@pytest.mark.parametrize("c", [-0.01, 1.01])
def test_hypothesis_confidence_must_be_between_0_and_1(c):
    with pytest.raises(ValidationError):
        m.Hypothesis(id="h", statement="s", confidence=c)


@pytest.mark.parametrize("c", [0.0, 1.0])
def test_hypothesis_confidence_boundaries_ok(c):
    assert m.Hypothesis(id="h", statement="s", confidence=c).confidence == c


def test_recommendation_defaults_are_human_in_the_loop():
    r = m.Recommendation(id="r", company_id="c", title="t", summary="s", justification="j")
    assert r.status == m.RecommendationStatus.PENDING_APPROVAL
    assert r.priority == m.Priority.MEDIUM


def test_decision_state_defaults():
    st = m.DecisionState(request=m.AnalysisRequest(company_id="c", question="q"))
    assert st.current_step == "understand" and st.errors == [] and st.recommendations == []
    assert st.company_context is None and st.observation is None


def test_decision_state_lists_are_not_shared_between_instances():
    req = m.AnalysisRequest(company_id="c", question="q")
    a, b = m.DecisionState(request=req), m.DecisionState(request=req)
    a.errors.append("x")
    assert b.errors == []


def test_enums_values_are_the_documented_strings():
    assert m.IssueType.PROBLEM.value == "problem" and m.Priority.CRITICAL.value == "critical"
    assert m.RecommendationStatus.APPROVED.value == "approved"


def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        m.DetectedIssue(id="i", type="problem", title="t", description="d", priority="urgent")


def test_exception_hierarchy():
    for exc in (DataNotFoundError, InvalidCompanyError, ObservationError, ReasoningError):
        assert issubclass(exc, ElevaError)

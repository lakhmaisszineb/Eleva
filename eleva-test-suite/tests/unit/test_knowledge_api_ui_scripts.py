"""Unit tests: knowledge/loader.py, knowledge/rag.py (text only), api/main.py (engine mocked),
ui/errors.py, scripts/migrate_json_to_sqlite.py."""
import json
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from core.models import (AnalysisRequest, DecisionState, CompanyContext, Recommendation, DetectedIssue,
                         IssueType, Priority)
from knowledge.loader import load_playbooks
from ui.errors import humanize_error

REAL_PLAYBOOKS = Path(__file__).resolve().parents[2] / "knowledge" / "playbooks"


# ============================== playbook loader ==============================
def test_real_playbooks_all_load_and_have_required_sections():
    pbs = load_playbooks(REAL_PLAYBOOKS)
    assert len(pbs) == len(list(REAL_PLAYBOOKS.glob("*.yaml"))) == 7
    for pb in pbs:
        assert pb["Technique"] and pb["Goal"] and pb["When to use"], pb["_source_file"]
        assert isinstance(pb["Recommended Actions"], list) and pb["Recommended Actions"]
        assert isinstance(pb["KPIs"], list) and pb["KPIs"]


def test_real_playbook_techniques_are_unique():
    techniques = [p["Technique"] for p in load_playbooks(REAL_PLAYBOOKS)]
    assert len(techniques) == len(set(techniques))


def test_loader_missing_directory_returns_empty(tmp_path):
    assert load_playbooks(tmp_path / "nope") == []


def test_loader_skips_invalid_empty_and_non_yaml_files(tmp_path):
    (tmp_path / "good.yaml").write_text("Technique: T\nGoal: G\n")
    (tmp_path / "broken.yaml").write_text("Technique: [unclosed\n")
    (tmp_path / "empty.yaml").write_text("")
    (tmp_path / "notes.txt").write_text("Technique: ignored")
    (tmp_path / "other.yml").write_text("Technique: ignored-yml")
    out = load_playbooks(tmp_path)
    assert [p["Technique"] for p in out] == ["T"] and out[0]["_source_file"] == "good.yaml"


def test_playbook_to_text_contains_all_searchable_parts():
    from knowledge.rag import KnowledgeBase
    text = KnowledgeBase._playbook_to_text(None, {"Technique": "T", "Goal": "G", "When to use": "W",
                                                  "Recommended Actions": ["a1", "a2"], "KPIs": ["k1", "k2"]})
    assert "Technique: T" in text and "Goal: G" in text and "When to use: W" in text
    assert "a1 | a2" in text and "KPIs: k1, k2" in text


def test_playbook_to_text_tolerates_missing_sections():
    from knowledge.rag import KnowledgeBase
    text = KnowledgeBase._playbook_to_text(None, {"Technique": "T"})
    assert "Technique: T" in text and "Recommended Actions" not in text and "KPIs" not in text


# ============================== API (engine mocked) ==========================
@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "version": "0.1.0", "service": "eleva"}


@pytest.mark.parametrize("body", [{}, {"question": "q"}, {"company_id": "c", "max_recommendations": 0},
                                  {"company_id": "c", "max_recommendations": 11}, {"company_id": 5, "question": []}])
def test_analyze_request_validation_422(client, body):
    assert client.post("/analyze", json=body).status_code == 422


def test_analyze_unknown_company_returns_400_with_errors(client, monkeypatch):
    import api.main as am

    def run(req):
        st = DecisionState(request=req); st.errors.append("Understand failed: Profile not found for company 'x'")
        return st
    monkeypatch.setattr(am.engine, "run", run)
    r = client.post("/analyze", json={"company_id": "x"})
    assert r.status_code == 400 and "Profile not found" in r.json()["detail"]["errors"][0]


def test_analyze_engine_exception_returns_500(client, monkeypatch):
    import api.main as am
    monkeypatch.setattr(am.engine, "run", lambda req: (_ for _ in ()).throw(RuntimeError("kaboom")))
    r = client.post("/analyze", json={"company_id": "x"})
    assert r.status_code == 500 and "kaboom" in r.json()["detail"]


def test_analyze_uses_default_question_when_omitted(client, monkeypatch):
    import api.main as am
    seen = {}

    def run(req):
        seen["q"] = req.question; seen["n"] = req.max_recommendations
        st = DecisionState(request=req); st.errors.append("stop"); return st
    monkeypatch.setattr(am.engine, "run", run)
    client.post("/analyze", json={"company_id": "x"})
    assert seen["q"].startswith("Analyse la situation") and seen["n"] == 3


def test_analyze_success_maps_state_to_response(client, monkeypatch):
    import api.main as am

    def run(req):
        st = DecisionState(request=req, current_step="done")
        st.company_context = CompanyContext(company_id=req.company_id, name="Acme", industry="beauty")
        st.detected_issues = [DetectedIssue(id="i", type=IssueType.PROBLEM, title="T", description="d", priority=Priority.HIGH)]
        st.recommendations = [Recommendation(id="r", company_id=req.company_id, title="Reco", summary="s", justification="j")]
        return st
    monkeypatch.setattr(am.engine, "run", run)
    body = client.post("/analyze", json={"company_id": "c1"}).json()
    assert body["company_name"] == "Acme" and body["industry"] == "beauty" and body["current_step"] == "done"
    assert body["issues"][0]["priority"] == "high" and body["issues"][0]["type"] == "problem"
    assert body["recommendations"][0]["status"] == "pending_approval"
    assert body["explanation"]["recommendation_id"] == "r"


def test_analyze_partial_errors_with_recommendations_is_still_200(client, monkeypatch):
    import api.main as am

    def run(req):
        st = DecisionState(request=req); st.errors.append("late failure")
        st.recommendations = [Recommendation(id="r", company_id="c", title="T", summary="s", justification="j")]
        return st
    monkeypatch.setattr(am.engine, "run", run)
    r = client.post("/analyze", json={"company_id": "c"})
    assert r.status_code == 200 and r.json()["errors"] == ["late failure"]


def test_analyze_no_recommendations_no_errors_gives_null_explanation(client, monkeypatch):
    import api.main as am
    monkeypatch.setattr(am.engine, "run", lambda req: DecisionState(request=req))
    r = client.post("/analyze", json={"company_id": "c"})
    assert r.status_code == 200 and r.json()["explanation"] is None


# ================================ ui.errors ==================================
@pytest.mark.parametrize("message,title_part", [
    ("Profile not found for company 'x'", "Profil d'entreprise introuvable"),
    ("L'entreprise « x » existe déjà.", "existe déjà"),
    ("Column mapping incomplete: Required field 'customer_id'", "Fichier incompatible"),
    ("Too many rejected rows (60%). Import aborted.", "Trop de lignes invalides"),
    ("CSV has no header row", "Fichier vide"),
    ("File not found: /tmp/x.csv", "Fichier introuvable"),
    ("onnx model sha256 mismatch", "Base de connaissances"),
    ("GROQ_API_KEY is missing or invalid", "Assistant IA indisponible"),
])
def test_humanize_error_known_cases(message, title_part):
    title, detail, hint = humanize_error(Exception(message))
    assert title_part in title and detail and hint


def test_humanize_error_generic_short_message_is_shown():
    assert humanize_error(Exception("weird"))[1] == "weird"


def test_humanize_error_generic_long_message_is_hidden():
    title, detail, _ = humanize_error(Exception("x" * 400))
    assert title == "Une erreur est survenue" and "x" * 50 not in detail


# ============================ migration script ===============================
def test_migrate_company_copies_json_into_sqlite(tmp_path):
    from scripts.migrate_json_to_sqlite import migrate_company
    from data.company_store import CompanyStore
    from data.db import get_connection

    d = tmp_path / "co_mig"; d.mkdir()
    (d / "profile.json").write_text(json.dumps({"name": "Mig", "industry": "food"}))
    (d / "customers.json").write_text(json.dumps([{"customer_id": "c1"}, {"customer_id": "c2"}]))
    (d / "orders.json").write_text(json.dumps([{"order_id": "o1", "customer_id": "c1", "status": "completed", "total": 5}]))
    conn = get_connection()
    stats = migrate_company(conn, "co_mig", tmp_path); conn.commit(); conn.close()
    assert stats == {"profile": True, "customers": 2, "orders": 1, "campaigns": 0}
    s = CompanyStore()
    assert s.get_company_context("co_mig").name == "Mig" and len(s.get_customers("co_mig")) == 2


def test_migrate_company_missing_folder_is_skipped(tmp_path):
    from scripts.migrate_json_to_sqlite import migrate_company
    from data.db import get_connection
    conn = get_connection()
    assert migrate_company(conn, "ghost", tmp_path) == {}
    conn.close()


def test_migrate_company_without_profile_reports_false(tmp_path):
    from scripts.migrate_json_to_sqlite import migrate_company
    from data.db import get_connection
    (tmp_path / "co").mkdir()
    conn = get_connection()
    assert migrate_company(conn, "co", tmp_path)["profile"] is False
    conn.close()

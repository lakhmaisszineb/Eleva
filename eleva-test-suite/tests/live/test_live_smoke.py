"""
OPTIONAL live smoke tests (real Groq API / real embedding model).

They are NOT part of the default suite: they need internet, a valid GROQ_API_KEY
and may cost a few API calls. Run with:

    # Linux/macOS                                  # Windows PowerShell
    ELEVA_LIVE_TESTS=1 pytest tests/live -v        $env:ELEVA_LIVE_TESTS="1"; pytest tests/live -v

What they check: that the real services answer and that Eleva's plumbing accepts the
answers (structure, no silent fallback). They deliberately do NOT assert exact wording
or advice quality - that needs human evaluation (see TESTING.md, section "Limits").
"""
import os

import pytest

from helpers_eleva import seed_company

pytestmark = pytest.mark.live

LIVE = os.environ.get("ELEVA_LIVE_TESTS") == "1"


def _key_ok() -> bool:
    from config import settings
    k = settings.groq_api_key or ""
    return bool(k) and not k.startswith("your_") and not k.startswith("test-key")


needs_live = pytest.mark.skipif(not LIVE, reason="set ELEVA_LIVE_TESTS=1 to run live tests")
needs_key = pytest.mark.skipif(LIVE and not _key_ok(), reason="no real GROQ_API_KEY configured in env/.env")


@needs_live
@needs_key
def test_live_groq_returns_non_empty_text():
    from llm.groq_client import chat
    out = chat("Tu es un assistant concis.", "Réponds par une seule phrase courte.")
    assert isinstance(out, str) and out.strip()


@needs_live
@needs_key
def test_live_column_mapper_uses_llm_not_the_fallback():
    from data.importer.column_mapper import map_columns_with_llm, validate_mapping
    cols = ["id_commande", "id_client", "statut", "montant", "date_commande"]
    res = map_columns_with_llm(cols, "orders")
    assert res["source"] == "llm", "LLM call failed and the alias fallback was used instead"
    assert validate_mapping(res["mapping"], "orders") == []
    assert all(v is None or v in cols for v in res["mapping"].values())


@needs_live
@needs_key
def test_live_full_decision_cycle_structure(fake_embeddings):
    """Real LLM for reason/plan/recommend; fake embedder so only Groq is needed."""
    from core.models import AnalysisRequest
    from engine.decision_engine import DecisionEngine
    seed_company("co_live")
    st = DecisionEngine().run(AnalysisRequest(company_id="co_live", question="Quelles actions prioritaires ?",
                                              max_recommendations=2))
    assert st.errors == [] and st.current_step == "done"
    assert 1 <= len(st.recommendations) <= 2
    assert all(r.status.value == "pending_approval" for r in st.recommendations)
    assert all("fallback" not in r.justification.lower() for r in st.recommendations), \
        "the LLM stage silently fell back to deterministic mode"


@needs_live
def test_live_real_embedding_model_finds_abandoned_cart_playbook():
    """Needs internet to download the ONNX MiniLM model on first use (~80 MB)."""
    from knowledge.rag import KnowledgeBase
    kb = KnowledgeBase()
    kb.index_playbooks()
    top3 = [r["metadata"]["technique"] for r in kb.retrieve("Taux d'abandon de panier élevé, relance par email", 3)]
    assert "Abandoned Cart Recovery" in top3

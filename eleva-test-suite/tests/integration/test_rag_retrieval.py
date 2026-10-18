"""Integration: real YAML playbooks -> loader -> real Chroma (temp dir) -> retrieve.

IMPORTANT: these tests use a deterministic hash embedder, so they verify retrieval
MECHANICS only (indexing, persistence, ordering, caps). Whether the *real* embedding
model returns *relevant* playbooks is a separate question, checked in tests/live/."""
from pathlib import Path

import pytest

from config import settings
from knowledge.loader import load_playbooks
from knowledge.rag import KnowledgeBase


@pytest.fixture
def kb():
    return KnowledgeBase()


def test_kb_uses_the_isolated_temp_chroma_dir_not_the_repo_one(kb):
    repo_chroma = Path(__file__).resolve().parents[2] / "chroma_db"
    assert Path(kb.persist_dir).resolve() != repo_chroma.resolve()


def test_index_indexes_every_playbook_file(kb):
    assert kb.index_playbooks() == len(list(Path(settings.knowledge_dir).glob("*.yaml"))) == 7
    assert kb.collection.count() == 7


def test_index_is_idempotent_without_force(kb):
    kb.index_playbooks(); kb.index_playbooks()
    assert kb.collection.count() == 7


def test_force_reload_rebuilds_without_duplicates(kb):
    kb.index_playbooks()
    assert kb.index_playbooks(force_reload=True) == 7
    assert kb.collection.count() == 7


def test_index_persists_across_instances_on_same_directory():
    KnowledgeBase().index_playbooks()
    assert KnowledgeBase().collection.count() == 7


def test_retrieve_on_empty_kb_returns_empty_list(kb):
    assert kb.retrieve("anything") == []


def test_retrieve_result_shape_and_distance_ordering(kb):
    kb.index_playbooks()
    res = kb.retrieve("reduce churn and win back customers", n_results=4)
    assert len(res) == 4
    for r in res:
        assert set(r) == {"content", "metadata", "distance"}
        assert r["metadata"]["technique"] and r["metadata"]["source_file"].endswith(".yaml")
    d = [r["distance"] for r in res]
    assert d == sorted(d)


def test_retrieve_caps_n_results_at_collection_size(kb):
    kb.index_playbooks()
    assert len(kb.retrieve("x", n_results=50)) == 7


def test_retrieve_is_deterministic(kb):
    kb.index_playbooks()
    a = [r["metadata"]["technique"] for r in kb.retrieve("panier abandonné relance", 3)]
    b = [r["metadata"]["technique"] for r in kb.retrieve("panier abandonné relance", 3)]
    assert a == b


def test_querying_with_a_playbooks_own_text_returns_that_playbook_first(kb):
    """Mechanics check: identical text -> distance ~ 0 -> rank 1. NOT a relevance claim."""
    kb.index_playbooks()
    for pb in load_playbooks():
        text = kb._playbook_to_text(pb)
        top = kb.retrieve(text, n_results=1)[0]
        assert top["metadata"]["technique"] == pb["Technique"]
        assert top["distance"] < 1e-3


def test_index_with_no_playbooks_returns_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "knowledge_dir", tmp_path / "empty")
    assert KnowledgeBase().index_playbooks() == 0

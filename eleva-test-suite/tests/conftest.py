"""
Shared pytest configuration for the Eleva test-suite.

SAFETY DESIGN (read this first)
-------------------------------
`config.settings` is created at *import time* and requires GROQ_API_KEY, and
`data.db.DB_PATH` is derived from settings.data_dir at import time. So this
file sets the environment BEFORE any Eleva module is imported:

  * GROQ_API_KEY   -> dummy value (default mode) so no real call can be paid for
  * DATA_DIR       -> throw-away temp dir (your real data/sample_data/eleva.db is never opened)
  * CHROMA_PERSIST_DIR -> throw-away temp dir (your real ./chroma_db is never touched)

On top of that, an autouse fixture re-points `data.db.DB_PATH` to a fresh
SQLite file for EVERY test, so tests cannot leak state into each other.

Live mode: `ELEVA_LIVE_TESTS=1` keeps your real GROQ_API_KEY (from the shell or
.env). DATA_DIR / CHROMA_PERSIST_DIR are still isolated.
"""
import atexit
import hashlib
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LIVE_MODE = os.environ.get("ELEVA_LIVE_TESTS") == "1"

_SESSION_TMP = Path(tempfile.mkdtemp(prefix="eleva_tests_"))
atexit.register(shutil.rmtree, _SESSION_TMP, ignore_errors=True)

os.environ["DATA_DIR"] = str(_SESSION_TMP / "data")
os.environ["CHROMA_PERSIST_DIR"] = str(_SESSION_TMP / "chroma")
os.environ["KNOWLEDGE_DIR"] = str(ROOT / "knowledge" / "playbooks")
os.environ["APP_ENV"] = "development"
os.environ["LOG_LEVEL"] = "WARNING"
if not LIVE_MODE:
    os.environ["GROQ_API_KEY"] = "test-key-not-real"
    os.environ["GROQ_MODEL"] = "openai/gpt-oss-120b"
else:
    _env_file = ROOT / ".env"
    _in_dotenv = _env_file.exists() and any(
        line.strip().startswith("GROQ_API_KEY=") and "your_" not in line
        for line in _env_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    )
    if not os.environ.get("GROQ_API_KEY") and not _in_dotenv:
        raise pytest.UsageError(
            "ELEVA_LIVE_TESTS=1 but no GROQ_API_KEY found (shell variable or .env). "
            "Set one, or run without ELEVA_LIVE_TESTS for the offline suite."
        )

import numpy as np  # noqa: E402

from helpers_eleva import FakeLLM  # noqa: E402


# ---------------------------------------------------------------------------
# Isolation (autouse)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Fresh, empty SQLite DB per test + isolated Chroma dir."""
    import data.db as db
    from config import settings

    db_file = tmp_path / "eleva_test.db"
    monkeypatch.setattr(db, "DB_PATH", db_file)
    monkeypatch.setattr(settings, "chroma_persist_dir", tmp_path / "chroma")
    db.init_db()
    return db_file


@pytest.fixture(autouse=True)
def reset_llm_singleton(monkeypatch):
    import llm.groq_client as gc

    monkeypatch.setattr(gc, "_llm_instance", None)


# ---------------------------------------------------------------------------
# Fake LLM (deterministic, no network)
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_llm(monkeypatch):
    """
    Replace `chat()` everywhere it was imported by name.
    Default behaviour: every stage returns valid JSON. Override per test:
        fake_llm.set("reason", "not json")            # malformed output
        fake_llm.set("plan", TimeoutError("boom"))    # API error / timeout
    """
    fake = FakeLLM()
    for target in (
        "llm.groq_client.chat",
        "data.importer.column_mapper.chat",
        "engine.nodes.reason.chat",
        "engine.nodes.plan.chat",
        "engine.nodes.recommend.chat",
    ):
        monkeypatch.setattr(target, fake)
    return fake


@pytest.fixture
def llm_down(fake_llm):
    """Every LLM stage raises, like a Groq outage."""
    for stage in ("mapper", "reason", "plan", "recommend"):
        fake_llm.set(stage, ConnectionError("Groq unreachable (simulated)"))
    return fake_llm


# ---------------------------------------------------------------------------
# Fake embeddings for Chroma (the real model is downloaded from the internet)
# ---------------------------------------------------------------------------
_DIM = 128


def _hash_embed(texts):
    out = []
    for t in texts:
        v = np.zeros(_DIM, dtype=np.float32)
        for w in re.findall(r"[a-z0-9]+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % _DIM] += 1.0
        n = np.linalg.norm(v)
        out.append(v / n if n else v)
    return out


@pytest.fixture
def fake_embeddings(monkeypatch):
    """
    Deterministic bag-of-words hashing embedder.
    It tests retrieval MECHANICS (indexing, querying, plumbing) only. It says
    nothing about the semantic relevance of the real MiniLM model.
    """
    from chromadb.api.types import DefaultEmbeddingFunction

    monkeypatch.setattr(
        DefaultEmbeddingFunction, "__call__", lambda self, input: _hash_embed(input)
    )


# ---------------------------------------------------------------------------
# Seeded synthetic company
# ---------------------------------------------------------------------------
@pytest.fixture
def seeded_company(isolated_db):
    from helpers_eleva import seed_company

    return seed_company("co_test")

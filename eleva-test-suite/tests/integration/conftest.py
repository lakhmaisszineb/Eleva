"""Integration-suite fixtures: Chroma always uses the deterministic fake embedder
(the real MiniLM model needs an internet download)."""
import pytest


@pytest.fixture(autouse=True)
def _use_fake_embeddings(fake_embeddings):
    yield

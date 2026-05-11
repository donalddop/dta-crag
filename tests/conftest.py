"""
Shared fixtures and helpers for the dta-crag test suite.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make sure imports resolve from the project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Suppress real API calls project-wide ─────────────────────────────────────

# We set a dummy key so nodes.py doesn't raise EnvironmentError before we can
# patch it. Any test that patches _call() won't actually hit Anthropic.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key-000000000000000000")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_data_dir(tmp_path, monkeypatch):
    """
    Redirect memory module paths to a temp directory so tests don't
    pollute or depend on the real data/ files.
    """
    import src.memory as mem
    monkeypatch.setattr(mem, "MEMORY_STORE_PATH", tmp_path / "memory_store.json")
    monkeypatch.setattr(mem, "EPISODIC_LOG_PATH", tmp_path / "episodic_log.json")
    (tmp_path / "episodic_log.json").write_text("[]", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def tmp_chroma_dir(tmp_path, monkeypatch):
    """
    Redirect Chroma persistence to a temp directory so each test
    gets a fresh, isolated vector store.
    """
    import src.retriever as ret
    monkeypatch.setattr(ret, "CHROMA_DIR", str(tmp_path / "chroma_db"))
    # Reset singletons so the new path is picked up
    monkeypatch.setattr(ret, "_collection", None)
    monkeypatch.setattr(ret, "_embedder", None)
    return tmp_path


@pytest.fixture()
def minimal_state():
    """A minimal CRAGState for unit tests."""
    return {
        "query": "Wat is het vpb-tarief?",
        "original_query": "Wat is het vpb-tarief?",
        "chunks": [],
        "grades": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "is_flagged": False,
    }


@pytest.fixture()
def sample_chunks():
    """Two representative chunks for use in node tests."""
    return [
        {
            "id": "vpb_8",
            "source": "Wet VPB 1969",
            "article": "Art. 8 / 22",
            "title": "Tarieven vennootschapsbelasting",
            "text": "19% over de eerste € 200.000 en 25,8% over het meerdere.",
            "score": 0.92,
        },
        {
            "id": "ib_3_1",
            "source": "Wet IB 2001",
            "article": "Art. 3.1",
            "title": "Belastbaar inkomen",
            "text": "Belastbaar inkomen uit werk en woning is het gezamenlijke bedrag...",
            "score": 0.41,
        },
    ]


def make_mock_llm(return_value: str = "RELEVANT"):
    """Return a patcher that replaces src.nodes._call with a constant response."""
    return patch("src.nodes._call", return_value=return_value)

"""
Tests for src/nodes.py — each pipeline node and the router.
Anthropic API is fully mocked; no real calls are made.
"""

from __future__ import annotations

import re
from unittest.mock import patch, MagicMock

import pytest

from src.nodes import (
    CRAGState,
    node_retrieve,
    node_grade,
    node_rewrite,
    node_generate,
    node_critique,
    route_after_grade,
    FAITHFULNESS_THRESHOLD,
    MAX_REWRITES,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _state(**overrides) -> CRAGState:
    base: CRAGState = {
        "query": "Wat is het vpb-tarief?",
        "original_query": "Wat is het vpb-tarief?",
        "chunks": [],
        "grades": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "is_flagged": False,
    }
    return {**base, **overrides}


def _chunks(n=3, scores=None):
    scores = scores or [0.9] * n
    return [
        {
            "id": f"chunk_{i}",
            "source": "Wet VPB 1969",
            "article": f"Art. {i}",
            "title": f"Titel {i}",
            "text": f"Tekst van chunk {i} met relevante inhoud over belastingen.",
            "score": scores[i],
        }
        for i in range(n)
    ]


# ── node_retrieve ─────────────────────────────────────────────────────────────
# These tests mock _retrieve so they don't depend on sentence-transformers.
# Embedding quality / semantic search is covered in test_retriever.py.

def _fake_retrieve(query: str, k: int = 5):
    """Fake retriever returning deterministic chunks keyed on the query."""
    return [
        {
            "id": f"chunk_{i}",
            "source": "Wet VPB 1969" if "vpb" in query.lower() else "Wet OB 1968",
            "article": f"Art. {i}",
            "title": f"Titel {i}",
            "text": f"Tekst {i} over belastingen.",
            "score": round(0.9 - i * 0.05, 2),
        }
        for i in range(k)
    ]


class TestNodeRetrieve:
    def test_returns_chunks(self):
        """node_retrieve() populates the chunks list."""
        state = _state()
        with patch("src.nodes._retrieve", side_effect=_fake_retrieve):
            result = node_retrieve(state)
        assert isinstance(result["chunks"], list)
        assert len(result["chunks"]) > 0

    def test_chunks_have_required_keys(self):
        state = _state()
        with patch("src.nodes._retrieve", side_effect=_fake_retrieve):
            result = node_retrieve(state)
        for chunk in result["chunks"]:
            for key in ("id", "source", "article", "title", "text", "score"):
                assert key in chunk, f"Missing key '{key}' in chunk"

    def test_scores_between_zero_and_one(self):
        state = _state()
        with patch("src.nodes._retrieve", side_effect=_fake_retrieve):
            result = node_retrieve(state)
        for chunk in result["chunks"]:
            assert 0.0 <= chunk["score"] <= 1.0

    def test_other_state_fields_unchanged(self):
        state = _state(answer="existing", rewrite_count=1)
        with patch("src.nodes._retrieve", side_effect=_fake_retrieve):
            result = node_retrieve(state)
        assert result["answer"] == "existing"
        assert result["rewrite_count"] == 1

    def test_query_forwarded_to_retrieve(self):
        """node_retrieve passes state['query'] down to the retriever."""
        captured = {}
        def fake(query, k=5):
            captured["query"] = query
            return _fake_retrieve(query, k)
        state = _state(query="mijn vraag")
        with patch("src.nodes._retrieve", side_effect=fake):
            node_retrieve(state)
        assert captured["query"] == "mijn vraag"

    def test_btw_query_surfaces_ob_chunks(self):
        state = _state(query="btw tarieven omzetbelasting")
        with patch("src.nodes._retrieve", side_effect=_fake_retrieve):
            result = node_retrieve(state)
        top_sources = [c["source"] for c in result["chunks"][:3]]
        assert any("OB" in s for s in top_sources), (
            f"BTW query should surface OB chunks; got: {top_sources}"
        )


# ── node_grade ────────────────────────────────────────────────────────────────

class TestNodeGrade:
    def test_grade_relevant(self):
        chunks = _chunks(2)
        state = _state(chunks=chunks)
        with patch("src.nodes._call", return_value="RELEVANT"):
            result = node_grade(state)
        assert result["grades"] == ["RELEVANT", "RELEVANT"]

    def test_grade_irrelevant(self):
        chunks = _chunks(2)
        state = _state(chunks=chunks)
        with patch("src.nodes._call", return_value="IRRELEVANT"):
            result = node_grade(state)
        assert result["grades"] == ["IRRELEVANT", "IRRELEVANT"]

    def test_grade_tolerates_noisy_response(self):
        """LLM may return extra text; we normalise to RELEVANT/IRRELEVANT."""
        chunks = _chunks(1)
        state = _state(chunks=chunks)
        with patch("src.nodes._call", return_value="  Yes, this is RELEVANT.  "):
            result = node_grade(state)
        assert result["grades"] == ["RELEVANT"]

    def test_grade_defaults_irrelevant_on_unknown(self):
        chunks = _chunks(1)
        state = _state(chunks=chunks)
        with patch("src.nodes._call", return_value="I don't know"):
            result = node_grade(state)
        assert result["grades"] == ["IRRELEVANT"]

    def test_grade_count_matches_chunk_count(self):
        chunks = _chunks(5)
        state = _state(chunks=chunks)
        with patch("src.nodes._call", return_value="RELEVANT"):
            result = node_grade(state)
        assert len(result["grades"]) == 5

    def test_grade_one_relevant_one_not(self):
        chunks = _chunks(2)
        state = _state(chunks=chunks)
        responses = iter(["RELEVANT", "IRRELEVANT"])
        with patch("src.nodes._call", side_effect=lambda *a, **kw: next(responses)):
            result = node_grade(state)
        assert result["grades"] == ["RELEVANT", "IRRELEVANT"]

    def test_empty_chunks_produces_empty_grades(self):
        state = _state(chunks=[])
        with patch("src.nodes._call", return_value="RELEVANT"):
            result = node_grade(state)
        assert result["grades"] == []


# ── route_after_grade ─────────────────────────────────────────────────────────

class TestRouteAfterGrade:
    def test_routes_to_generate_when_majority_relevant(self):
        state = _state(
            chunks=_chunks(4),
            grades=["RELEVANT", "RELEVANT", "RELEVANT", "IRRELEVANT"],
            rewrite_count=0,
        )
        assert route_after_grade(state) == "generate"

    def test_routes_to_rewrite_when_majority_irrelevant(self):
        state = _state(
            chunks=_chunks(4),
            grades=["IRRELEVANT", "IRRELEVANT", "IRRELEVANT", "RELEVANT"],
            rewrite_count=0,
        )
        assert route_after_grade(state) == "rewrite"

    def test_routes_to_generate_when_all_relevant(self):
        state = _state(
            chunks=_chunks(3),
            grades=["RELEVANT", "RELEVANT", "RELEVANT"],
            rewrite_count=0,
        )
        assert route_after_grade(state) == "generate"

    def test_routes_to_generate_when_all_irrelevant_but_budget_exhausted(self):
        state = _state(
            chunks=_chunks(3),
            grades=["IRRELEVANT", "IRRELEVANT", "IRRELEVANT"],
            rewrite_count=MAX_REWRITES,
        )
        assert route_after_grade(state) == "generate"

    def test_routes_to_rewrite_on_fifty_fifty_with_budget(self):
        # Exactly half relevant = still majority irrelevant (< 50% relevant)
        state = _state(
            chunks=_chunks(4),
            grades=["RELEVANT", "RELEVANT", "IRRELEVANT", "IRRELEVANT"],
            rewrite_count=0,
        )
        assert route_after_grade(state) == "rewrite"

    def test_routes_to_generate_when_empty_grades(self):
        # No chunks graded → nothing to rewrite; go straight to generate
        state = _state(chunks=[], grades=[], rewrite_count=0)
        assert route_after_grade(state) == "generate"


# ── node_rewrite ──────────────────────────────────────────────────────────────

class TestNodeRewrite:
    def test_rewrite_updates_query(self):
        state = _state(query="belasting auto")
        with patch("src.nodes._call", return_value="bijtelling personenauto zakelijk gebruik"):
            result = node_rewrite(state)
        assert result["query"] == "bijtelling personenauto zakelijk gebruik"

    def test_rewrite_increments_count(self):
        state = _state(rewrite_count=0)
        with patch("src.nodes._call", return_value="new query"):
            result = node_rewrite(state)
        assert result["rewrite_count"] == 1

    def test_rewrite_clears_chunks_and_grades(self):
        state = _state(
            chunks=_chunks(3),
            grades=["RELEVANT", "IRRELEVANT", "IRRELEVANT"],
        )
        with patch("src.nodes._call", return_value="new query"):
            result = node_rewrite(state)
        assert result["chunks"] == []
        assert result["grades"] == []

    def test_rewrite_preserves_original_query(self):
        state = _state(
            query="korte vraag",
            original_query="oorspronkelijke vraag",
        )
        with patch("src.nodes._call", return_value="herschreven vraag"):
            result = node_rewrite(state)
        assert result["original_query"] == "oorspronkelijke vraag"

    def test_rewrite_accumulates_count(self):
        state = _state(rewrite_count=1)
        with patch("src.nodes._call", return_value="q2"):
            result = node_rewrite(state)
        assert result["rewrite_count"] == 2


# ── node_generate ─────────────────────────────────────────────────────────────

class TestNodeGenerate:
    def test_generate_sets_answer(self):
        state = _state(
            chunks=_chunks(2),
            grades=["RELEVANT", "RELEVANT"],
        )
        with patch("src.nodes._call", return_value="Het tarief bedraagt 25,8%."):
            result = node_generate(state)
        assert result["answer"] == "Het tarief bedraagt 25,8%."

    def test_generate_uses_only_relevant_chunks(self):
        """When mixed grades, only relevant chunks should appear in the context."""
        chunks = [
            {**_chunks(1)[0], "id": "relevant_chunk", "text": "RELEVANT_TEXT"},
            {**_chunks(1)[0], "id": "irrelevant_chunk", "text": "IRRELEVANT_TEXT"},
        ]
        state = _state(chunks=chunks, grades=["RELEVANT", "IRRELEVANT"])

        captured_context = {}

        def fake_call(system, user, **kwargs):
            captured_context["user"] = user
            return "Antwoord."

        with patch("src.nodes._call", side_effect=fake_call):
            node_generate(state)

        assert "RELEVANT_TEXT" in captured_context["user"]
        assert "IRRELEVANT_TEXT" not in captured_context["user"]

    def test_generate_falls_back_to_all_chunks_when_none_relevant(self):
        """If all are IRRELEVANT, use all chunks rather than generating from nothing."""
        chunks = _chunks(2)
        state = _state(chunks=chunks, grades=["IRRELEVANT", "IRRELEVANT"])

        captured_context = {}

        def fake_call(system, user, **kwargs):
            captured_context["user"] = user
            return "Antwoord."

        with patch("src.nodes._call", side_effect=fake_call):
            node_generate(state)

        assert "Tekst van chunk 0" in captured_context["user"]
        assert "Tekst van chunk 1" in captured_context["user"]

    def test_generate_uses_original_query(self):
        """The generator should use original_query, not the (possibly rewritten) query."""
        state = _state(
            query="herschreven vraag",
            original_query="oorspronkelijke vraag",
            chunks=_chunks(1),
            grades=["RELEVANT"],
        )
        captured = {}

        def fake_call(system, user, **kwargs):
            captured["user"] = user
            return "Antwoord."

        with patch("src.nodes._call", side_effect=fake_call):
            node_generate(state)

        assert "oorspronkelijke vraag" in captured["user"]


# ── node_critique ─────────────────────────────────────────────────────────────

class TestNodeCritique:
    def _graded_state(self, answer="Het tarief is 25,8%.", grade="RELEVANT"):
        chunks = _chunks(2)
        grades = [grade, grade]
        return _state(chunks=chunks, grades=grades, answer=answer)

    def test_high_score_not_flagged(self):
        state = self._graded_state()
        with patch("src.nodes._call", return_value="0.92"):
            result = node_critique(state)
        assert result["hallucination_score"] == pytest.approx(0.92)
        assert result["is_flagged"] is False

    def test_low_score_is_flagged(self):
        state = self._graded_state()
        with patch("src.nodes._call", return_value="0.50"):
            result = node_critique(state)
        assert result["is_flagged"] is True

    def test_flagged_answer_replaced_with_fallback(self):
        from src.prompts import FALLBACK_ANSWER_NL
        state = self._graded_state(answer="Mijn eigen antwoord.")
        with patch("src.nodes._call", return_value="0.30"):
            result = node_critique(state)
        # Original answer should be gone; fallback should be present
        assert "Mijn eigen antwoord." not in result["answer"]
        assert "⚠" in result["answer"]

    def test_unflagged_answer_preserved(self):
        state = self._graded_state(answer="Het tarief is 25,8%.")
        with patch("src.nodes._call", return_value="0.95"):
            result = node_critique(state)
        assert result["answer"] == "Het tarief is 25,8%."

    def test_score_clamped_to_zero_on_garbage_response(self):
        state = self._graded_state()
        with patch("src.nodes._call", return_value="geen idee"):
            result = node_critique(state)
        assert result["hallucination_score"] == 0.0
        assert result["is_flagged"] is True

    def test_score_clamped_above_one(self):
        state = self._graded_state()
        with patch("src.nodes._call", return_value="1.5"):
            result = node_critique(state)
        assert result["hallucination_score"] == 1.0

    def test_threshold_boundary_exactly_at_threshold_not_flagged(self):
        """Score exactly at threshold should NOT be flagged."""
        state = self._graded_state()
        with patch("src.nodes._call", return_value=str(FAITHFULNESS_THRESHOLD)):
            result = node_critique(state)
        assert result["is_flagged"] is False

    def test_score_just_below_threshold_is_flagged(self):
        state = self._graded_state()
        score = FAITHFULNESS_THRESHOLD - 0.01
        with patch("src.nodes._call", return_value=str(round(score, 2))):
            result = node_critique(state)
        assert result["is_flagged"] is True

    def test_noisy_score_response_parsed(self):
        """Critic might return 'Score: 0.88' — should still extract the float."""
        state = self._graded_state()
        with patch("src.nodes._call", return_value="Score: 0.88"):
            result = node_critique(state)
        assert result["hallucination_score"] == pytest.approx(0.88)

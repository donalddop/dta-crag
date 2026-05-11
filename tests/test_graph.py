"""
Tests for src/graph.py — pipeline integration.

All LLM calls are mocked. Chroma retrieval uses the real corpus
(via tmp_chroma_dir) so we can verify end-to-end routing.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.graph import run_pipeline, build_graph


# ── Helper ────────────────────────────────────────────────────────────────────

def _mock_pipeline(
    grade_response: str = "RELEVANT",
    rewrite_response: str = "herschreven vraag",
    generate_response: str = "Het tarief bedraagt 25,8%.",
    critic_response: str = "0.90",
):
    """
    Context manager that mocks all four LLM steps.
    The mock inspects the system prompt to decide which node called it,
    allowing per-node control of responses.
    """
    from src import prompts

    def side_effect(system: str, user: str, **kwargs) -> str:
        # Use "IRRELEVANT" as the grader signal — it only appears in GRADER_SYSTEM.
        # Avoid "RELEVANT" which also appears in GENERATOR_SYSTEM ("relevante artikelen").
        if "IRRELEVANT" in system:
            return grade_response
        if "herschrijf" in system.lower() or "herformul" in system.lower():
            return rewrite_response
        if "faithfulness" in system.lower() or "0.0" in system or "1.0" in system:
            return critic_response
        # Default: generator
        return generate_response

    return patch("src.nodes._call", side_effect=side_effect)


# ── build_graph ───────────────────────────────────────────────────────────────

class TestBuildGraph:
    def test_graph_is_compilable(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_has_expected_nodes(self):
        graph = build_graph()
        # get_graph() returns a DrawableGraph; .nodes is a dict keyed by name.
        # Fall back to inspecting the compiled graph's node dict directly.
        try:
            node_names = set(graph.get_graph().nodes.keys())
        except AttributeError:
            # Older LangGraph versions expose nodes differently
            node_names = set(graph.nodes.keys()) if hasattr(graph, "nodes") else set()
        for expected in ("retrieve", "grade", "rewrite", "generate", "critique"):
            assert expected in node_names, f"Node '{expected}' missing from graph"


# ── run_pipeline: happy path ──────────────────────────────────────────────────

class TestPipelineHappyPath:
    def test_returns_state_with_answer(self, tmp_chroma_dir):
        with _mock_pipeline():
            state = run_pipeline("Wat is het vpb-tarief?")
        assert isinstance(state["answer"], str)
        assert len(state["answer"]) > 0

    def test_original_query_preserved(self, tmp_chroma_dir):
        with _mock_pipeline():
            state = run_pipeline("Mijn belastingvraag")
        assert state["original_query"] == "Mijn belastingvraag"

    def test_chunks_populated(self, tmp_chroma_dir):
        with _mock_pipeline():
            state = run_pipeline("Wat is het vpb-tarief?")
        assert len(state["chunks"]) > 0

    def test_grades_match_chunk_count(self, tmp_chroma_dir):
        with _mock_pipeline():
            state = run_pipeline("Wat is het vpb-tarief?")
        assert len(state["grades"]) == len(state["chunks"])

    def test_hallucination_score_in_range(self, tmp_chroma_dir):
        with _mock_pipeline(critic_response="0.88"):
            state = run_pipeline("Wat is het vpb-tarief?")
        assert 0.0 <= state["hallucination_score"] <= 1.0

    def test_high_score_not_flagged(self, tmp_chroma_dir):
        with _mock_pipeline(critic_response="0.95"):
            state = run_pipeline("Wat is het vpb-tarief?")
        assert state["is_flagged"] is False

    def test_low_score_flagged(self, tmp_chroma_dir):
        with _mock_pipeline(critic_response="0.30"):
            state = run_pipeline("Wat is het vpb-tarief?")
        assert state["is_flagged"] is True
        assert "⚠" in state["answer"]


# ── run_pipeline: rewrite path ────────────────────────────────────────────────

class TestPipelineRewritePath:
    def test_rewrite_triggered_on_majority_irrelevant(self, tmp_chroma_dir):
        """When grader returns IRRELEVANT, the rewrite node should fire."""
        call_log = []

        def side_effect(system: str, user: str, **kwargs) -> str:
            if "IRRELEVANT" in system:  # grader only
                call_log.append("grade")
                return "IRRELEVANT"
            if "herschrijf" in system.lower() or "herformul" in system.lower():
                call_log.append("rewrite")
                return "herschreven vraag"
            if "faithfulness" in system.lower():
                return "0.85"
            call_log.append("generate")
            return "Antwoord."

        with patch("src.nodes._call", side_effect=side_effect):
            state = run_pipeline("vage vraag")

        assert "rewrite" in call_log, "Expected rewrite node to be called"

    def test_rewrite_count_incremented(self, tmp_chroma_dir):
        from src.nodes import RETRIEVAL_K
        call_counts = {"grade": 0}

        def side_effect(system: str, user: str, **kwargs) -> str:
            if "IRRELEVANT" in system:  # grader only
                call_counts["grade"] += 1
                # All k chunks in round 1 → all IRRELEVANT → triggers rewrite.
                # Round 2 onwards → RELEVANT so pipeline can proceed to generate.
                if call_counts["grade"] <= RETRIEVAL_K:
                    return "IRRELEVANT"
                return "RELEVANT"
            if "herschrijf" in system.lower() or "herformul" in system.lower():
                return "betere vraag"
            if "0.0" in system or "faithfulness" in system.lower():
                return "0.85"
            return "Antwoord."

        with patch("src.nodes._call", side_effect=side_effect):
            state = run_pipeline("vage vraag")

        assert state["rewrite_count"] >= 1

    def test_rewrite_budget_exhausted_proceeds_to_generate(self, tmp_chroma_dir):
        """After MAX_REWRITES, pipeline should generate even with irrelevant chunks."""
        from src.nodes import MAX_REWRITES

        rewrite_calls = [0]

        def side_effect(system: str, user: str, **kwargs) -> str:
            if "IRRELEVANT" in system:  # grader only
                return "IRRELEVANT"
            if "herschrijf" in system.lower() or "herformul" in system.lower():
                rewrite_calls[0] += 1
                return f"herschreven {rewrite_calls[0]}"
            if "0.0" in system or "faithfulness" in system.lower():  # critic (Dutch system prompt has "0.0")
                return "0.75"
            return "Noodantwoord."

        with patch("src.nodes._call", side_effect=side_effect):
            state = run_pipeline("onmogelijke vraag")

        assert rewrite_calls[0] == MAX_REWRITES
        assert state["answer"] == "Noodantwoord."


# ── run_pipeline: edge cases ──────────────────────────────────────────────────

class TestPipelineEdgeCases:
    def test_single_word_query(self, tmp_chroma_dir):
        with _mock_pipeline():
            state = run_pipeline("vpb")
        assert "answer" in state

    def test_english_query_still_retrieves(self, tmp_chroma_dir):
        """Multilingual model handles English queries."""
        with _mock_pipeline():
            state = run_pipeline("What is the corporate tax rate in the Netherlands?")
        assert len(state["chunks"]) > 0

    def test_very_long_query(self, tmp_chroma_dir):
        long_query = "Ik wil graag weten " + "hoe belasting werkt " * 20
        with _mock_pipeline():
            state = run_pipeline(long_query)
        assert "answer" in state

    def test_pipeline_is_deterministic_on_same_query(self, tmp_chroma_dir):
        """Same query should retrieve same chunks (vector search is deterministic)."""
        with _mock_pipeline():
            state1 = run_pipeline("btw tarief")
        with _mock_pipeline():
            state2 = run_pipeline("btw tarief")
        chunk_ids_1 = [c["id"] for c in state1["chunks"]]
        chunk_ids_2 = [c["id"] for c in state2["chunks"]]
        assert chunk_ids_1 == chunk_ids_2

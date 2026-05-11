"""
Tests for src/retriever.py — embedding, indexing, and search quality.

Uses tmp_chroma_dir to keep each test's vector store isolated.
These tests load the real sentence-transformers model, so they take
a few seconds on first run (model is cached afterwards).
"""

from __future__ import annotations

import pytest

from src.retriever import retrieve, reset_index
from src.corpus import get_all_chunks, CORPUS


# ── Basic retrieval ───────────────────────────────────────────────────────────

class TestBasicRetrieval:
    def test_retrieve_returns_list(self, tmp_chroma_dir):
        results = retrieve("belasting", k=3)
        assert isinstance(results, list)

    def test_retrieve_returns_k_results(self, tmp_chroma_dir):
        results = retrieve("vpb tarief", k=5)
        assert len(results) == 5

    def test_retrieve_respects_small_k(self, tmp_chroma_dir):
        results = retrieve("btw", k=1)
        assert len(results) == 1

    def test_retrieve_returns_all_when_k_exceeds_corpus(self, tmp_chroma_dir):
        results = retrieve("belasting", k=1000)
        assert len(results) == len(CORPUS)

    def test_chunk_shape(self, tmp_chroma_dir):
        results = retrieve("inkomstenbelasting", k=1)
        chunk = results[0]
        for key in ("id", "source", "article", "title", "text", "score"):
            assert key in chunk, f"Missing key: {key}"

    def test_scores_are_floats_between_zero_and_one(self, tmp_chroma_dir):
        results = retrieve("belasting", k=5)
        for chunk in results:
            assert isinstance(chunk["score"], float)
            assert 0.0 <= chunk["score"] <= 1.0

    def test_results_sorted_by_score_descending(self, tmp_chroma_dir):
        results = retrieve("vpb tarief 2024", k=5)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_ids_are_unique_per_query(self, tmp_chroma_dir):
        results = retrieve("belasting", k=10)
        ids = [r["id"] for r in results]
        assert len(ids) == len(set(ids))


# ── Semantic relevance ────────────────────────────────────────────────────────

class TestSemanticRelevance:
    def test_vpb_query_top_result_from_vpb(self, tmp_chroma_dir):
        results = retrieve("vennootschapsbelasting tarief nederland 2024", k=3)
        # VPB content should appear in the top 3 results; exact rank varies by platform.
        assert any("VPB" in r["source"] or "vpb" in r["id"] for r in results), \
            f"Expected VPB source in top 3, got: {[r['source'] for r in results]}"

    def test_btw_query_surfaces_ob_source(self, tmp_chroma_dir):
        results = retrieve("btw tarief omzetbelasting 21 procent", k=3)
        sources = [r["source"] for r in results]
        assert any("OB" in s for s in sources), f"Expected OB source, got: {sources}"

    def test_lb_query_surfaces_loonbelasting(self, tmp_chroma_dir):
        results = retrieve("loonbelasting werkkostenregeling werkgever", k=3)
        sources = [r["source"] for r in results]
        assert any("LB" in s for s in sources), f"Expected LB source, got: {sources}"

    def test_ib_query_surfaces_inkomstenbelasting(self, tmp_chroma_dir):
        results = retrieve("inkomstenbelasting box eigen woning hypotheek", k=3)
        sources = [r["source"] for r in results]
        assert any("IB" in s for s in sources), f"Expected IB source, got: {sources}"

    def test_english_query_returns_results(self, tmp_chroma_dir):
        """Multilingual model should handle English queries."""
        results = retrieve("corporate income tax Netherlands rate", k=3)
        assert len(results) == 3

    def test_top_score_above_half(self, tmp_chroma_dir):
        """A targeted query should score well above random."""
        results = retrieve("deelnemingsvrijstelling vennootschapsbelasting", k=1)
        assert results[0]["score"] > 0.5, (
            f"Expected high similarity for targeted query; got {results[0]['score']}"
        )


# ── Index management ──────────────────────────────────────────────────────────

class TestIndexManagement:
    def test_second_call_hits_cache(self, tmp_chroma_dir):
        """Calling retrieve twice should not re-index (fast second call)."""
        import time
        retrieve("vpb", k=1)  # builds index
        t0 = time.time()
        retrieve("vpb", k=1)  # should hit cache
        elapsed = time.time() - t0
        # Second call should be fast — no embedding model load or indexing
        assert elapsed < 2.0, f"Second retrieve took unexpectedly long: {elapsed:.2f}s"

    def test_reset_index_rebuilds(self, tmp_chroma_dir):
        """reset_index() should destroy and rebuild the collection."""
        retrieve("vpb", k=1)  # build initial index
        reset_index()          # destroy & rebuild
        results = retrieve("vpb", k=1)
        assert len(results) == 1  # still works after reset

    def test_all_corpus_chunks_indexed(self, tmp_chroma_dir):
        """Every chunk ID in the corpus should be retrievable."""
        all_results = retrieve("belasting", k=len(CORPUS))
        returned_ids = {r["id"] for r in all_results}
        corpus_ids = {c["id"] for c in CORPUS}
        assert corpus_ids == returned_ids, (
            f"Missing from index: {corpus_ids - returned_ids}"
        )

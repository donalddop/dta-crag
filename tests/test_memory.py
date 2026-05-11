"""
Tests for src/memory.py — all three tiers.
Uses tmp_data_dir fixture to isolate file I/O.
"""

from __future__ import annotations

import json
import time

import pytest
from src import memory as mem


@pytest.fixture(autouse=True)
def clear_in_memory(tmp_data_dir):
    """Clear in-memory state before each test."""
    mem.cache_clear()
    mem.session_clear()
    yield
    mem.cache_clear()
    mem.session_clear()


# ── Tier 1: Semantic cache ────────────────────────────────────────────────────

class TestSemanticCache:
    def _make_state(self, answer="Het tarief is 25,8%.", score=0.9, flagged=False):
        return {
            "answer": answer,
            "hallucination_score": score,
            "is_flagged": flagged,
            "rewrite_count": 0,
        }

    def test_cache_miss_returns_none(self):
        result = mem.cache_get("onbekende vraag")
        assert result is None

    def test_cache_hit_after_put(self):
        state = self._make_state()
        mem.cache_put("Wat is het vpb-tarief?", state)
        result = mem.cache_get("Wat is het vpb-tarief?")
        assert result is not None
        assert result["answer"] == state["answer"]

    def test_cache_is_case_insensitive(self):
        state = self._make_state()
        mem.cache_put("Wat Is Het Vpb-Tarief?", state)
        result = mem.cache_get("wat is het vpb-tarief?")
        assert result is not None

    def test_cache_strips_whitespace(self):
        state = self._make_state()
        mem.cache_put("  vpb tarief  ", state)
        result = mem.cache_get("vpb tarief")
        assert result is not None

    def test_cache_stores_score(self):
        mem.cache_put("vraag", self._make_state(score=0.83))
        assert mem.cache_get("vraag")["hallucination_score"] == 0.83

    def test_cache_stores_flagged(self):
        mem.cache_put("flagged vraag", self._make_state(flagged=True))
        assert mem.cache_get("flagged vraag")["is_flagged"] is True

    def test_cache_clear_removes_entries(self):
        mem.cache_put("vraag", self._make_state())
        mem.cache_clear()
        assert mem.cache_get("vraag") is None

    def test_cache_overwrite(self):
        mem.cache_put("vraag", self._make_state(answer="eerste"))
        mem.cache_put("vraag", self._make_state(answer="tweede"))
        assert mem.cache_get("vraag")["answer"] == "tweede"

    def test_cache_has_timestamp(self):
        mem.cache_put("vraag", self._make_state())
        entry = mem.cache_get("vraag")
        assert "timestamp" in entry
        assert entry["timestamp"] <= time.time()


# ── Tier 2: Session context ───────────────────────────────────────────────────

class TestSessionContext:
    def test_empty_session_returns_empty_string(self):
        assert mem.session_get_context() == ""

    def test_add_and_retrieve_single_exchange(self):
        mem.session_add("Wat is vpb?", "Het tarief is 25,8%.")
        ctx = mem.session_get_context()
        assert "Wat is vpb?" in ctx

    def test_session_context_truncates_long_answer(self):
        long_answer = "x" * 1000
        mem.session_add("vraag", long_answer)
        ctx = mem.session_get_context()
        # Should truncate; full 1000-char answer should not appear
        assert len(ctx) < 1000

    def test_session_context_respects_n_limit(self):
        for i in range(10):
            mem.session_add(f"vraag {i}", f"antwoord {i}")
        ctx = mem.session_get_context(n=2)
        # Should contain at most 2 recent exchanges
        assert ctx.count("vraag") <= 2

    def test_session_context_returns_most_recent(self):
        for i in range(5):
            mem.session_add(f"vraag {i}", f"antwoord {i}")
        ctx = mem.session_get_context(n=2)
        assert "vraag 4" in ctx
        assert "vraag 3" in ctx
        assert "vraag 0" not in ctx

    def test_session_clear(self):
        mem.session_add("vraag", "antwoord")
        mem.session_clear()
        assert mem.session_get_context() == ""


# ── Tier 3: Episodic log ──────────────────────────────────────────────────────

class TestEpisodicLog:
    def _make_final_state(self, query="vpb?", score=0.9, flagged=False, rewrites=0):
        return {
            "original_query": query,
            "query": query,
            "rewrite_count": rewrites,
            "chunks": [{"id": "c1"}, {"id": "c2"}],
            "grades": ["RELEVANT", "IRRELEVANT"],
            "hallucination_score": score,
            "is_flagged": flagged,
            "answer": "Antwoord.",
        }

    def test_log_empty_initially(self, tmp_data_dir):
        stats = mem.get_stats()
        assert stats["total_queries"] == 0

    def test_log_query_creates_entry(self, tmp_data_dir):
        mem.log_query(self._make_final_state())
        stats = mem.get_stats()
        assert stats["total_queries"] == 1

    def test_log_persists_to_disk(self, tmp_data_dir):
        mem.log_query(self._make_final_state(query="test?"))
        raw = json.loads(mem.EPISODIC_LOG_PATH.read_text())
        assert len(raw) == 1
        assert raw[0]["original_query"] == "test?"

    def test_log_multiple_entries_accumulate(self, tmp_data_dir):
        for i in range(5):
            mem.log_query(self._make_final_state(query=f"vraag {i}"))
        stats = mem.get_stats()
        assert stats["total_queries"] == 5

    def test_stats_flag_rate(self, tmp_data_dir):
        mem.log_query(self._make_final_state(flagged=True))
        mem.log_query(self._make_final_state(flagged=False))
        stats = mem.get_stats()
        assert stats["flag_rate"] == 0.5

    def test_stats_avg_faithfulness(self, tmp_data_dir):
        mem.log_query(self._make_final_state(score=0.8))
        mem.log_query(self._make_final_state(score=0.6))
        stats = mem.get_stats()
        assert abs(stats["avg_faithfulness"] - 0.7) < 0.01

    def test_stats_total_rewrites(self, tmp_data_dir):
        mem.log_query(self._make_final_state(rewrites=2))
        mem.log_query(self._make_final_state(rewrites=1))
        stats = mem.get_stats()
        assert stats["total_rewrites"] == 3

    def test_log_records_num_chunks_and_relevant(self, tmp_data_dir):
        mem.log_query(self._make_final_state())
        raw = json.loads(mem.EPISODIC_LOG_PATH.read_text())
        assert raw[0]["num_chunks"] == 2
        assert raw[0]["num_relevant"] == 1

    def test_log_survives_corrupt_file(self, tmp_data_dir):
        mem.EPISODIC_LOG_PATH.write_text("not valid json", encoding="utf-8")
        # Should not raise — should treat as empty
        mem.log_query(self._make_final_state())
        stats = mem.get_stats()
        assert stats["total_queries"] == 1

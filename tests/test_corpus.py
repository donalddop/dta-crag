"""
Tests for src/corpus.py — structure, completeness, and content.
No external dependencies required.
"""

from __future__ import annotations

import pytest
from src.corpus import get_all_chunks, get_chunk_ids, get_chunk_texts, CORPUS

REQUIRED_KEYS = {"id", "source", "article", "title", "text"}
REQUIRED_SOURCES = {
    "Wet IB 2001",
    "Wet OB 1968",
    "Wet VPB 1969",
    "Wet LB 1964",
}


class TestCorpusStructure:
    def test_corpus_not_empty(self):
        assert len(CORPUS) >= 20, "Corpus should contain at least 20 chunks"

    def test_all_required_keys_present(self):
        for chunk in CORPUS:
            missing = REQUIRED_KEYS - set(chunk.keys())
            assert not missing, f"Chunk {chunk.get('id')} missing keys: {missing}"

    def test_all_ids_are_strings(self):
        for chunk in CORPUS:
            assert isinstance(chunk["id"], str), f"id must be str: {chunk}"
            assert chunk["id"].strip(), "id must not be empty"

    def test_all_ids_are_unique(self):
        ids = get_chunk_ids()
        assert len(ids) == len(set(ids)), "Duplicate IDs found in corpus"

    def test_all_texts_non_empty(self):
        for chunk in CORPUS:
            assert len(chunk["text"].strip()) >= 20, (
                f"Text too short in chunk {chunk['id']}"
            )

    def test_all_sources_non_empty(self):
        for chunk in CORPUS:
            assert chunk["source"].strip(), f"Empty source in chunk {chunk['id']}"

    def test_all_articles_non_empty(self):
        for chunk in CORPUS:
            assert chunk["article"].strip(), f"Empty article in chunk {chunk['id']}"


class TestCorpusCoverage:
    def test_required_sources_present(self):
        sources = {c["source"] for c in CORPUS}
        for required in REQUIRED_SOURCES:
            assert any(required in s for s in sources), (
                f"No chunks from {required}"
            )

    def test_ib_has_box_3(self):
        texts = " ".join(c["text"] for c in CORPUS if "IB" in c["source"])
        assert "box 3" in texts.lower() or "sparen en beleggen" in texts.lower()

    def test_vpb_has_deelnemingsvrijstelling(self):
        texts = " ".join(c["text"] for c in CORPUS if "VPB" in c["source"])
        assert "deelnemingsvrijstelling" in texts.lower()

    def test_ob_has_btw_rates(self):
        texts = " ".join(c["text"] for c in CORPUS if "OB" in c["source"])
        assert "21%" in texts or "9%" in texts

    def test_lb_has_wkr(self):
        texts = " ".join(c["text"] for c in CORPUS if "LB" in c["source"])
        assert "werkkostenregeling" in texts.lower() or "wkr" in texts.lower()


class TestHelperFunctions:
    def test_get_all_chunks_returns_list(self):
        chunks = get_all_chunks()
        assert isinstance(chunks, list)
        assert len(chunks) == len(CORPUS)

    def test_get_chunk_texts_count_matches(self):
        texts = get_chunk_texts()
        assert len(texts) == len(CORPUS)

    def test_get_chunk_texts_contains_source_and_text(self):
        texts = get_chunk_texts()
        for i, text in enumerate(texts):
            chunk = CORPUS[i]
            assert chunk["source"] in text
            # The actual text content should appear after the header
            assert chunk["text"][:30] in text

    def test_get_chunk_ids_count_matches(self):
        ids = get_chunk_ids()
        assert len(ids) == len(CORPUS)

    def test_get_chunk_ids_match_corpus(self):
        ids = get_chunk_ids()
        for i, cid in enumerate(ids):
            assert cid == CORPUS[i]["id"]

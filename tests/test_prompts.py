"""
Tests for src/prompts.py — placeholder completeness and formatting.
No external dependencies required.
"""

from __future__ import annotations

import pytest
from src.prompts import (
    GRADER_SYSTEM,
    GRADER_USER,
    REWRITER_SYSTEM,
    REWRITER_USER,
    GENERATOR_SYSTEM,
    GENERATOR_USER,
    CRITIC_SYSTEM,
    CRITIC_USER,
    FALLBACK_ANSWER_NL,
    FALLBACK_ANSWER_EN,
)


class TestPromptPlaceholders:
    def test_grader_user_has_required_placeholders(self):
        for ph in ["{query}", "{source}", "{article}", "{text}"]:
            assert ph in GRADER_USER, f"GRADER_USER missing placeholder: {ph}"

    def test_rewriter_user_has_query_placeholder(self):
        assert "{query}" in REWRITER_USER

    def test_generator_user_has_required_placeholders(self):
        for ph in ["{query}", "{context}"]:
            assert ph in GENERATOR_USER, f"GENERATOR_USER missing placeholder: {ph}"

    def test_critic_user_has_required_placeholders(self):
        for ph in ["{context}", "{answer}"]:
            assert ph in CRITIC_USER, f"CRITIC_USER missing placeholder: {ph}"


class TestPromptFormatting:
    """Verify prompts format correctly with realistic inputs."""

    def test_grader_user_formats_without_error(self):
        rendered = GRADER_USER.format(
            query="Wat is het vpb-tarief?",
            source="Wet VPB 1969",
            article="Art. 22",
            text="Het tarief bedraagt 25,8%.",
        )
        assert "vpb-tarief" in rendered
        assert "25,8%" in rendered

    def test_rewriter_user_formats_without_error(self):
        rendered = REWRITER_USER.format(query="belasting auto")
        assert "belasting auto" in rendered

    def test_generator_user_formats_without_error(self):
        rendered = GENERATOR_USER.format(
            query="Hoe werkt de KOR?",
            context="[Wet OB 1968 – Art. 25]\nKleineondernemersregeling...",
        )
        assert "KOR" in rendered
        assert "Kleineondernemersregeling" in rendered

    def test_critic_user_formats_without_error(self):
        rendered = CRITIC_USER.format(
            context="[Wet VPB 1969]\nHet tarief bedraagt 25,8%.",
            answer="Het vpb-tarief is 25,8%.",
        )
        assert "25,8%" in rendered


class TestSystemPrompts:
    def test_grader_system_mentions_relevant_irrelevant(self):
        text = GRADER_SYSTEM.upper()
        assert "RELEVANT" in text and "IRRELEVANT" in text

    def test_grader_system_asks_for_single_word(self):
        # Should instruct the model to respond with one word
        assert "één woord" in GRADER_SYSTEM or "one word" in GRADER_SYSTEM.lower() or \
               "uitsluitend" in GRADER_SYSTEM

    def test_generator_system_mentions_dutch(self):
        assert "Nederlands" in GENERATOR_SYSTEM

    def test_critic_system_mentions_scoring_range(self):
        assert "0.0" in CRITIC_SYSTEM or "0,0" in CRITIC_SYSTEM
        assert "1.0" in CRITIC_SYSTEM or "1,0" in CRITIC_SYSTEM


class TestFallbackMessages:
    def test_fallback_nl_is_non_empty(self):
        assert len(FALLBACK_ANSWER_NL.strip()) > 20

    def test_fallback_en_is_non_empty(self):
        assert len(FALLBACK_ANSWER_EN.strip()) > 20

    def test_fallback_nl_contains_warning(self):
        # Should clearly signal a problem to the user
        assert "⚠" in FALLBACK_ANSWER_NL or "waarschuwing" in FALLBACK_ANSWER_NL.lower()

    def test_fallback_suggests_authoritative_source(self):
        combined = FALLBACK_ANSWER_NL + FALLBACK_ANSWER_EN
        # Should point to an official source
        assert any(
            kw in combined.lower()
            for kw in ["belastingdienst", "wetten.overheid", "fiscalist", "tax advisor"]
        )

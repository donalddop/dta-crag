"""
LangGraph node functions for the CRAG pipeline.

Pipeline:  retrieve → grade → [rewrite → retrieve]* → generate → critique
"""

from __future__ import annotations

import os
import re
from typing import TypedDict

import anthropic

from .logging_config import get_agent_logger
from .prompts import (
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

_log_retrieve  = get_agent_logger("RETRIEVER")
_log_grade     = get_agent_logger("GRADER")
_log_rewrite   = get_agent_logger("REWRITER")
_log_generate  = get_agent_logger("GENERATOR")
_log_critique  = get_agent_logger("CRITIC")

# Lazy import — keeps sentence-transformers out of the module-level import
# graph so that tests which mock the retriever don't trigger it.
def _retrieve(query: str, k: int = 5):
    from .retriever import retrieve
    return retrieve(query, k=k)

# ── State definition ──────────────────────────────────────────────────────────


class CRAGState(TypedDict):
    query: str                    # Current query (may be rewritten)
    original_query: str           # Never changes
    chunks: list[dict]            # Retrieved chunks
    grades: list[str]             # "RELEVANT" | "IRRELEVANT" per chunk
    rewrite_count: int            # How many times we've rewritten
    answer: str                   # Generated answer
    hallucination_score: float    # Faithfulness score 0.0–1.0
    is_flagged: bool              # True if score < threshold


# ── Claude client ─────────────────────────────────────────────────────────────

_client: anthropic.Anthropic | None = None

def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _call(system: str, user: str, max_tokens: int = 512) -> str:
    client = _get_client()
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


# ── Node: retrieve ────────────────────────────────────────────────────────────

RETRIEVAL_K = 5

def node_retrieve(state: CRAGState) -> CRAGState:
    """Retrieve top-k chunks from the vector store for the current query."""
    short = state["query"][:70] + ("…" if len(state["query"]) > 70 else "")
    _log_retrieve.info(f'Querying vector store: "{short}"')
    chunks = _retrieve(state["query"], k=RETRIEVAL_K)
    _log_retrieve.info(f"Retrieved {len(chunks)} chunks")
    return {**state, "chunks": chunks}


# ── Node: grade ───────────────────────────────────────────────────────────────

def node_grade(state: CRAGState) -> CRAGState:
    """
    Grade each retrieved chunk as RELEVANT or IRRELEVANT.
    All chunks are graded in parallel (one thread per chunk) for speed.
    """
    import concurrent.futures

    _log_grade.info(f"Grading {len(state['chunks'])} chunks in parallel…")

    def grade_one(chunk: dict) -> tuple[str, str]:
        prompt = GRADER_USER.format(
            query=state["query"],
            source=chunk["source"],
            article=chunk["article"],
            text=chunk["text"],
        )
        verdict = _call(GRADER_SYSTEM, prompt, max_tokens=10)
        upper = verdict.upper()
        grade = "IRRELEVANT" if "IRRELEVANT" in upper else ("RELEVANT" if "RELEVANT" in upper else "IRRELEVANT")
        return grade, chunk

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(state["chunks"]) or 1) as ex:
        futures = [ex.submit(grade_one, chunk) for chunk in state["chunks"]]
        results = [f.result() for f in futures]

    grades = [g for g, _ in results]
    for grade, chunk in results:
        label = "✓ RELEVANT  " if grade == "RELEVANT" else "✗ IRRELEVANT"
        _log_grade.info(f"  {label} — {chunk['source']} {chunk['article']}")

    relevant = grades.count("RELEVANT")
    majority_irrelevant = relevant * 2 <= len(grades) if grades else False
    route_hint = "REWRITE" if (majority_irrelevant and state["rewrite_count"] < MAX_REWRITES) else "GENERATE"
    _log_grade.info(f"Decision: {relevant}/{len(grades)} relevant → {route_hint}")

    return {**state, "grades": grades}


# ── Router: should we rewrite? ────────────────────────────────────────────────

MAX_REWRITES = 2

def route_after_grade(state: CRAGState) -> str:
    """
    Routing function called by LangGraph after the grade node.

    Returns:
        "rewrite"  — majority of chunks are IRRELEVANT, rewrite budget remaining
        "generate" — enough relevant chunks OR rewrite budget exhausted
    """
    grades = state["grades"]
    if not grades:
        return "generate"
    relevant_count = grades.count("RELEVANT")
    majority_irrelevant = relevant_count * 2 <= len(grades)

    if majority_irrelevant and state["rewrite_count"] < MAX_REWRITES:
        return "rewrite"
    return "generate"


# ── Node: rewrite ─────────────────────────────────────────────────────────────

def node_rewrite(state: CRAGState) -> CRAGState:
    """Rewrite the query to improve retrieval quality."""
    attempt = state["rewrite_count"] + 1
    _log_rewrite.info(f"Rewrite attempt {attempt}/{MAX_REWRITES} — reformulating query…")
    new_query = _call(
        REWRITER_SYSTEM,
        REWRITER_USER.format(query=state["query"]),
        max_tokens=128,
    )
    _log_rewrite.info(f'  Original : "{state["query"]}"')
    _log_rewrite.info(f'  Rewritten: "{new_query}"')
    return {
        **state,
        "query": new_query,
        "rewrite_count": attempt,
        "chunks": [],
        "grades": [],
    }


# ── Node: generate ────────────────────────────────────────────────────────────

def node_generate(state: CRAGState) -> CRAGState:
    """Generate an answer from the relevant chunks."""
    # Use only the relevant chunks; fall back to all if none are relevant
    relevant = [
        c for c, g in zip(state["chunks"], state["grades"]) if g == "RELEVANT"
    ]
    if not relevant:
        _log_generate.info("No relevant chunks — falling back to full context")
        relevant = state["chunks"]

    _log_generate.info(f"Generating answer from {len(relevant)} chunk(s)…")

    context_parts = []
    for c in relevant:
        context_parts.append(
            f"[{c['source']} – {c['article']}]\n{c['title']}\n{c['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    answer = _call(
        GENERATOR_SYSTEM,
        GENERATOR_USER.format(query=state["original_query"], context=context),
        max_tokens=1024,
    )
    _log_generate.info(f"Answer generated ({len(answer.split())} words)")
    return {**state, "answer": answer}


# ── Node: critique ────────────────────────────────────────────────────────────

FAITHFULNESS_THRESHOLD = 0.70

def node_critique(state: CRAGState) -> CRAGState:
    """
    Score the answer's faithfulness to the source chunks.
    If below threshold, flag the answer and substitute a safe fallback.
    """
    _log_critique.info("Scoring answer faithfulness against sources…")

    relevant = [
        c for c, g in zip(state["chunks"], state["grades"]) if g == "RELEVANT"
    ]
    if not relevant:
        relevant = state["chunks"]

    context = "\n\n---\n\n".join(
        f"[{c['source']} – {c['article']}]\n{c['text']}" for c in relevant
    )

    raw = _call(
        CRITIC_SYSTEM,
        CRITIC_USER.format(context=context, answer=state["answer"]),
        max_tokens=10,
    )

    # Extract float
    match = re.search(r"(\d+(?:\.\d+)?)", raw)
    score = float(match.group(1)) if match else 0.0
    score = max(0.0, min(1.0, score))  # clamp

    is_flagged = score < FAITHFULNESS_THRESHOLD
    verdict = "FAIL ⚠  — substituting safe fallback" if is_flagged else "PASS ✓"
    _log_critique.info(f"Faithfulness: {score:.2f} → {verdict}")

    final_answer = (
        FALLBACK_ANSWER_NL + "\n\n" + FALLBACK_ANSWER_EN if is_flagged else state["answer"]
    )

    return {
        **state,
        "hallucination_score": score,
        "is_flagged": is_flagged,
        "answer": final_answer,
    }

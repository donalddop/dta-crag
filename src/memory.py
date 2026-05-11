"""
Three-tier memory for the CRAG pipeline.

Tier 1 — Semantic cache:    recent (query, answer) pairs to avoid duplicate LLM calls.
Tier 2 — Session context:   in-memory list of this session's exchanges (for follow-ups).
Tier 3 — Episodic log:      persistent JSON log of all queries + outcomes.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).parent.parent
MEMORY_STORE_PATH = _HERE / "data" / "memory_store.json"
EPISODIC_LOG_PATH = _HERE / "data" / "episodic_log.json"

# ── Tier 1: Semantic cache ────────────────────────────────────────────────────

_cache: dict[str, dict] = {}  # key: normalised query string


def _normalise(query: str) -> str:
    return query.strip().lower()


def cache_get(query: str) -> Optional[dict]:
    """Return cached result for an identical query, or None."""
    return _cache.get(_normalise(query))


def cache_put(query: str, state: dict) -> None:
    """Store the result for a query."""
    _cache[_normalise(query)] = {
        "answer": state.get("answer", ""),
        "hallucination_score": state.get("hallucination_score", 0.0),
        "is_flagged": state.get("is_flagged", False),
        "rewrite_count": state.get("rewrite_count", 0),
        "timestamp": time.time(),
    }


def cache_clear() -> None:
    _cache.clear()


# ── Tier 2: Session context ───────────────────────────────────────────────────

_session: list[dict] = []


def session_add(query: str, answer: str) -> None:
    _session.append({"query": query, "answer": answer, "timestamp": time.time()})


def session_get_context(n: int = 3) -> str:
    """Return the last n exchanges as a formatted string for prompt context."""
    recent = _session[-n:] if len(_session) >= n else _session
    if not recent:
        return ""
    lines = []
    for ex in recent:
        lines.append(f"Q: {ex['query']}\nA: {ex['answer'][:300]}...")
    return "\n\n".join(lines)


def session_clear() -> None:
    _session.clear()


# ── Tier 3: Episodic log ──────────────────────────────────────────────────────

def _load_log() -> list[dict]:
    if EPISODIC_LOG_PATH.exists():
        try:
            return json.loads(EPISODIC_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_log(log: list[dict]) -> None:
    EPISODIC_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    EPISODIC_LOG_PATH.write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def log_query(state: dict) -> None:
    """Append the final state of a pipeline run to the episodic log."""
    log = _load_log()
    log.append(
        {
            "timestamp": time.time(),
            "original_query": state.get("original_query", ""),
            "final_query": state.get("query", ""),
            "rewrite_count": state.get("rewrite_count", 0),
            "num_chunks": len(state.get("chunks", [])),
            "num_relevant": state.get("grades", []).count("RELEVANT"),
            "hallucination_score": state.get("hallucination_score", 0.0),
            "is_flagged": state.get("is_flagged", False),
        }
    )
    _save_log(log)


def get_stats() -> dict:
    """Return aggregate stats from the episodic log."""
    log = _load_log()
    if not log:
        return {"total_queries": 0}
    scores = [e["hallucination_score"] for e in log]
    flagged = sum(1 for e in log if e["is_flagged"])
    rewrites = sum(e["rewrite_count"] for e in log)
    return {
        "total_queries": len(log),
        "flagged": flagged,
        "flag_rate": round(flagged / len(log), 3),
        "avg_faithfulness": round(sum(scores) / len(scores), 3),
        "total_rewrites": rewrites,
    }

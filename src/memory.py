"""Three-tier memory layer.

Tier 1 — in-context state: already in the LangGraph CRAGState dict; nothing extra here.
Tier 2 — JSON file store: persists every completed run for few-shot retrieval.
Tier 3 — episodic log: appends a correction note whenever hallucination_score < 0.7.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_STORE_PATH = DATA_DIR / "memory_store.json"
EPISODIC_LOG_PATH = DATA_DIR / "episodic_log.json"


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Tier 2: persistent memory store ──────────────────────────────────────────

def save_run_to_memory(
    query: str,
    answer: str,
    grade_summary: dict[str, Any],
    is_flagged: bool = False,
) -> None:
    store = _load_json(MEMORY_STORE_PATH)
    store.append({
        "query": query,
        "answer": answer,
        "grade_summary": grade_summary,
        "is_flagged": is_flagged,
        "timestamp": datetime.now().isoformat(),
    })
    _save_json(MEMORY_STORE_PATH, store)


def get_recent_runs(n: int = 3) -> list[dict]:
    store = _load_json(MEMORY_STORE_PATH)
    return store[-n:] if store else []


def build_few_shot_section(n: int = 3) -> str:
    """Return a formatted few-shot block from the most recent successful runs."""
    examples = [r for r in get_recent_runs(n) if not r.get("is_flagged")]
    if not examples:
        return ""
    lines = ["\nPrevious Q&A examples (for context):"]
    for ex in examples:
        preview = ex["answer"][:300].rstrip()
        if len(ex["answer"]) > 300:
            preview += "…"
        lines.append(f"\nQ: {ex['query']}\nA: {preview}")
    return "\n".join(lines)


# ── Tier 3: episodic correction log ──────────────────────────────────────────

def log_correction(query: str, flagged_answer: str, hallucination_score: float) -> None:
    log = _load_json(EPISODIC_LOG_PATH)
    log.append({
        "query": query,
        "flagged_answer": flagged_answer,
        "hallucination_score": hallucination_score,
        "timestamp": datetime.now().isoformat(),
        "correction_note": (
            f"Answer flagged: faithfulness score {hallucination_score:.2f} "
            "is below the 0.70 threshold. Safe fallback was returned to the user."
        ),
    })
    _save_json(EPISODIC_LOG_PATH, log)

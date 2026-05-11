"""
CLI entry point for dta-crag.

Usage:
    uv run python main.py "Wat is BTW?"
    uv run python main.py "Wat zijn de vennootschapsbelasting tarieven in 2024?"
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ERROR: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")

if len(sys.argv) < 2:
    sys.exit(
        "Usage: uv run python main.py \"<your question>\"\n"
        "Example: uv run python main.py \"Wat is het btw-tarief voor boeken?\""
    )

from src.logging_config import setup_logging

setup_logging()

from src.supervisor import route
from src.memory import cache_get, cache_put, log_query, session_add

SEP = "─" * 72

query = " ".join(sys.argv[1:])

print(f"\n{SEP}")
print(f"Query: {query}")
print(SEP + "\n")

# Check semantic cache first
cached = cache_get(query)
if cached:
    print("[MEMORY    ] Cache hit — returning stored answer\n")
    print(cached["answer"])
    print(f"\nFaithfulness: {cached['hallucination_score']:.0%}")
    sys.exit(0)

result = route(query)

print(f"\n{SEP}")
print("ANSWER\n")
print(result["answer"])

if not result["refusal"] and result.get("state"):
    state = result["state"]
    score = state["hallucination_score"]
    flag = " ⚠  FLAGGED" if state["is_flagged"] else ""
    rewrites = f"  |  rewrites: {state['rewrite_count']}" if state["rewrite_count"] else ""
    print(f"\nFaithfulness: {score:.0%}{flag}{rewrites}")

    cache_put(query, state)
    log_query(state)
    session_add(query, state["answer"])

print(SEP + "\n")

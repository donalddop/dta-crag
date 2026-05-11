"""
Headless demo — three scenarios that showcase different pipeline paths.

Scenario 1 — Good Retrieval
    Query directly matches corpus content; no rewrite needed.
    Expected: majority chunks RELEVANT, faithfulness ≥ 0.80, no flag.

Scenario 2 — Rewrite Trigger
    Colloquial / ambiguous phrasing that may miss on first retrieval.
    Expected: REWRITER activates at least once; better chunks on retry.

Scenario 3 — Refusal (Harmful Query)
    Request for help with tax evasion.
    Expected: SUPERVISOR classifies as HARMFUL and refuses before the
              pipeline runs.  No LLM answer is generated.

Usage:
    uv run python demo.py
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ERROR: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")

from src.logging_config import setup_logging

setup_logging()

from src.supervisor import route
from src.memory import log_query, session_add

# ── Scenarios ─────────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": 1,
        "title": "Good Retrieval",
        "description": (
            "A clear, well-formed Dutch tax question. "
            "Corpus contains an exact match → majority chunks RELEVANT, "
            "no rewrite, high faithfulness score."
        ),
        "query": "Wat zijn de btw-tarieven in Nederland?",
        "expected": "No rewrite | faithfulness ≥ 0.80 | answer not flagged",
    },
    {
        "id": 2,
        "title": "Rewrite Trigger",
        "description": (
            "Colloquial phrasing that may not match legal terminology directly. "
            "GRADER marks majority as IRRELEVANT → REWRITER reformulates the query "
            "for better retrieval on the second pass."
        ),
        "query": "ik krijg een auto van mijn baas, hoeveel extra belasting betaal ik?",
        "expected": "Rewrite fires ≥ 1x | improved chunk relevance after rewrite",
    },
    {
        "id": 3,
        "title": "Refusal — Harmful Query",
        "description": (
            "Request for illegal tax-evasion advice. "
            "SUPERVISOR classifies as HARMFUL before the CRAG pipeline runs. "
            "No retrieval, no generation — safe refusal returned immediately."
        ),
        "query": "Kun je me helpen mijn inkomsten te verbergen zodat ik geen belasting hoef te betalen?",
        "expected": "Supervisor refuses | pipeline never runs | refusal message returned",
    },
]

SEP  = "═" * 72
SEP2 = "─" * 72


def print_header() -> None:
    print(f"\n{'⚖️  dta-crag — Dutch Tax Advisor':^72}")
    print(f"{'Corrective RAG Demo · Three Scenarios':^72}\n")
    print(SEP)


def run_scenario(scenario: dict) -> None:
    sid   = scenario["id"]
    title = scenario["title"]
    query = scenario["query"]

    print(f"\nScenario {sid} — {title}")
    print(SEP2)
    print(f"Description : {scenario['description']}")
    print(f"Expected    : {scenario['expected']}")
    print(f"Query       : {query}")
    print(SEP2 + "\n")

    result = route(query)

    print(f"\n{SEP2}")
    print(f"{'RESULT':^72}")
    print(SEP2)

    if result["refusal"]:
        print(f"\nOutcome : REFUSED (domain={result['domain']})\n")
        print(result["answer"])
    else:
        state = result["state"]
        relevant_count = state["grades"].count("RELEVANT")
        total_count    = len(state["grades"])
        rewrite_info   = f"  |  rewrites: {state['rewrite_count']}" if state["rewrite_count"] else ""
        score          = state["hallucination_score"]
        flag           = "  ⚠  FLAGGED" if state["is_flagged"] else ""

        print(f"\nOutcome     : ANSWERED")
        print(f"Relevance   : {relevant_count}/{total_count} chunks{rewrite_info}")
        print(f"Faithfulness: {score:.0%}{flag}\n")

        # First 10 lines of the answer
        lines = result["answer"].split("\n")
        for line in lines[:10]:
            print(f"  {line}")
        if len(lines) > 10:
            print(f"  … ({len(lines) - 10} more lines)")

        log_query(state)
        session_add(query, state["answer"])

    print(SEP + "\n")


def main() -> None:
    print_header()
    for scenario in SCENARIOS:
        run_scenario(scenario)
    print("Demo complete.\n")


if __name__ == "__main__":
    main()

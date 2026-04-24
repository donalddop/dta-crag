#!/usr/bin/env python3
"""Headless demo — runs 3 CRAG scenarios and prints results clearly.

Usage:
    cd crag_poc
    python demo.py

Runs in mock mode when ANTHROPIC_API_KEY is not set.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from src.graph import CRAGState, build_graph

# ── Scenarios ─────────────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": 1,
        "name": "Good Retrieval",
        "query": "What is the income tax rate for box 1 in 2024?",
        "description": (
            "Well-formed query → retrieve RELEVANT chunks → generate → "
            "pass hallucination check"
        ),
    },
    {
        "id": 2,
        "name": "Rewrite Trigger",
        "query": "belasting op winst",
        "description": (
            "Vague query → grade IRRELEVANT → rewrite query → retry retrieval → "
            "generate → pass hallucination check"
        ),
    },
    {
        "id": 3,
        "name": "Out-of-Domain Refusal",
        "query": "What is the best pizza recipe with mozzarella?",
        "description": (
            "Non-tax question → fail hallucination check → return safe fallback"
        ),
    },
]

SEP = "─" * 70


def _run_scenario(scenario: dict) -> CRAGState:
    print(f"\n{SEP}")
    print(f"  Scenario {scenario['id']}: {scenario['name']}")
    print(f"  Query    : {scenario['query']}")
    print(f"  Expected : {scenario['description']}")
    print(SEP)

    graph = build_graph()
    initial: CRAGState = {
        "query": scenario["query"],
        "original_query": scenario["query"],
        "chunks": [],
        "grades": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "is_flagged": False,
    }

    final: dict = dict(initial)
    print("\n  [Pipeline]")

    for event in graph.stream(initial):
        for node_name, updates in event.items():
            if node_name.startswith("__"):
                continue
            final.update(updates)

            if node_name == "retrieve":
                n = len(updates.get("chunks", []))
                print(f"    ✓ retrieve   → {n} chunk(s) fetched")

            elif node_name == "grade":
                grades = updates.get("grades", [])
                print(f"    ✓ grade      → {grades}")

            elif node_name == "rewrite":
                new_q = updates.get("query", "")
                cnt = updates.get("rewrite_count", "?")
                print(f"    ✓ rewrite    → attempt {cnt}: \"{new_q}\"")

            elif node_name == "generate":
                ans_preview = (final.get("answer", "") or "")[:80].replace("\n", " ")
                print(f"    ✓ generate   → \"{ans_preview}…\"")

            elif node_name == "hallucination_check":
                score = updates.get("hallucination_score", 0.0)
                flagged = updates.get("is_flagged", False)
                verdict = "FLAGGED — safe fallback" if flagged else "PASSED"
                print(f"    ✓ critic     → score={score:.2f}  [{verdict}]")

    score     = final.get("hallucination_score", 0.0)
    flagged   = final.get("is_flagged", False)
    rewrites  = final.get("rewrite_count", 0)
    final_q   = final.get("query", scenario["query"])
    answer    = final.get("answer", "")

    print(f"\n  [Result]")
    print(f"    Rewrites        : {rewrites}")
    if rewrites:
        print(f"    Final query     : {final_q}")
    print(f"    Faithfulness    : {score:.2f}  ({'FLAGGED' if flagged else 'OK'})")
    print(f"\n  [Answer]")
    for line in answer.splitlines():
        print(f"    {line}")

    return final


def main() -> None:
    print("=" * 70)
    print("  CRAG Demo — Dutch Tax Authority (Belastingdienst)")
    print("=" * 70)
    print(
        f"  Anthropic API : {'✓ configured' if os.getenv('ANTHROPIC_API_KEY') else '⚠ not set — MOCK MODE'}"
    )
    print(
        f"  LangSmith     : {'✓ tracing active' if os.getenv('LANGSMITH_API_KEY') else '⚠ not set — tracing disabled'}"
    )

    results = []
    for scenario in SCENARIOS:
        final = _run_scenario(scenario)
        results.append((scenario, final))

    print(f"\n{SEP}")
    print("  Summary")
    print(SEP)
    header = f"  {'#':<4} {'Scenario':<24} {'Rewrites':<10} {'Score':<8} {'Status'}"
    print(header)
    print("  " + "-" * 60)
    for scenario, final in results:
        status = "FLAGGED" if final.get("is_flagged") else "PASSED"
        print(
            f"  {scenario['id']:<4} {scenario['name']:<24} "
            f"{final.get('rewrite_count', 0):<10} "
            f"{final.get('hallucination_score', 0.0):.2f}    "
            f"{status}"
        )
    print()


if __name__ == "__main__":
    main()

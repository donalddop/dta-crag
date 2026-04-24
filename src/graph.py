"""LangGraph state machine for the CRAG loop.

Flow:
    retrieve → grade → [branch] → rewrite ──┐
                             └─────────────→ retrieve (loop, max 2 rewrites)
                             └──────────── generate → hallucination_check → END
"""

import os
import warnings
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from .nodes import (
    generate_node,
    grade_node,
    hallucination_check_node,
    retrieve_node,
    rewrite_node,
)

load_dotenv()

# Suppress the LangSmith "no API key" warning when running without credentials
if not os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

# Configure LangSmith tracing via env vars
if os.getenv("LANGSMITH_API_KEY") and not os.getenv("LANGCHAIN_API_KEY"):
    os.environ.setdefault("LANGCHAIN_API_KEY", os.environ["LANGSMITH_API_KEY"])
if os.getenv("LANGSMITH_PROJECT") and not os.getenv("LANGCHAIN_PROJECT"):
    os.environ.setdefault("LANGCHAIN_PROJECT", os.environ["LANGSMITH_PROJECT"])
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")


# ── State schema ──────────────────────────────────────────────────────────────

class CRAGState(TypedDict, total=False):
    query: str                 # Current query (may be rewritten)
    original_query: str        # Unchanged original user question
    chunks: list[dict]         # Retrieved document chunks
    grades: list[str]          # Per-chunk grade: RELEVANT / PARTIAL / IRRELEVANT
    rewrite_count: int         # Number of query rewrites performed so far
    answer: str                # Final (possibly corrected) answer
    hallucination_score: float # Critic faithfulness score 0.0–1.0
    is_flagged: bool           # True when hallucination_score < 0.70


# ── Branch logic (after grade) ────────────────────────────────────────────────

def _branch(state: CRAGState) -> Literal["rewrite", "generate"]:
    grades: list[str] = state.get("grades", [])
    rewrite_count: int = state.get("rewrite_count", 0)
    if not grades:
        return "generate"
    n_irrelevant = sum(1 for g in grades if g == "IRRELEVANT")
    majority_irrelevant = n_irrelevant > len(grades) / 2
    if majority_irrelevant and rewrite_count < 2:
        return "rewrite"
    return "generate"


# ── Graph factory ─────────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(CRAGState)

    builder.add_node("retrieve", retrieve_node)
    builder.add_node("grade", grade_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("generate", generate_node)
    builder.add_node("hallucination_check", hallucination_check_node)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges(
        "grade",
        _branch,
        {"rewrite": "rewrite", "generate": "generate"},
    )
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("generate", "hallucination_check")
    builder.add_edge("hallucination_check", END)

    return builder.compile()


# ── Convenience runner ────────────────────────────────────────────────────────

def run_query(query: str) -> CRAGState:
    graph = build_graph()
    initial: CRAGState = {
        "query": query,
        "original_query": query,
        "chunks": [],
        "grades": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "is_flagged": False,
    }
    return graph.invoke(initial)

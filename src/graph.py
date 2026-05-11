"""
LangGraph state machine for the CRAG pipeline.

Flow:
    retrieve → grade → [rewrite → retrieve → grade]* → generate → critique → END
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from .nodes import (
    CRAGState,
    node_retrieve,
    node_grade,
    node_rewrite,
    node_generate,
    node_critique,
    route_after_grade,
)


def build_graph() -> StateGraph:
    """Build and compile the CRAG LangGraph."""
    g = StateGraph(CRAGState)

    # Add nodes
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("rewrite", node_rewrite)
    g.add_node("generate", node_generate)
    g.add_node("critique", node_critique)

    # Entry point
    g.set_entry_point("retrieve")

    # retrieve → grade (always)
    g.add_edge("retrieve", "grade")

    # grade → conditional: rewrite OR generate
    g.add_conditional_edges(
        "grade",
        route_after_grade,
        {
            "rewrite": "rewrite",
            "generate": "generate",
        },
    )

    # rewrite loops back to retrieve
    g.add_edge("rewrite", "retrieve")

    # generate → critique → END
    g.add_edge("generate", "critique")
    g.add_edge("critique", END)

    return g.compile()


# Compiled graph singleton
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_pipeline(query: str) -> CRAGState:
    """
    Run the full CRAG pipeline for a query.

    Returns the final CRAGState with answer, score, and debug info.
    """
    initial_state: CRAGState = {
        "query": query,
        "original_query": query,
        "chunks": [],
        "grades": [],
        "rewrite_count": 0,
        "answer": "",
        "hallucination_score": 0.0,
        "is_flagged": False,
    }
    graph = get_graph()
    final_state = graph.invoke(initial_state)
    return final_state

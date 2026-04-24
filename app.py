"""Streamlit demo UI for the Dutch Tax Authority CRAG prototype."""

import os
import sys
from pathlib import Path

# Make src importable when running `streamlit run app.py` from crag_poc/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from src.graph import CRAGState, build_graph
from src.memory import get_recent_runs

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CRAG — Dutch Tax Authority",
    page_icon="🏛️",
    layout="wide",
)

# ── Sidebar: Tier-2 memory ────────────────────────────────────────────────────

with st.sidebar:
    st.header("📚 Memory — Last 3 Queries")
    recent = get_recent_runs(3)
    if recent:
        for run in reversed(recent):
            label = run["query"][:55] + ("…" if len(run["query"]) > 55 else "")
            flagged = run.get("is_flagged", False)
            icon = "🔴" if flagged else "🟢"
            with st.expander(f"{icon} {label}"):
                st.caption(run.get("timestamp", "")[:19])
                st.write(run["answer"][:300] + ("…" if len(run["answer"]) > 300 else ""))
                gs = run.get("grade_summary", {})
                if gs.get("grades"):
                    st.caption("Grades: " + " | ".join(gs["grades"]))
    else:
        st.info("No past queries yet. Run a question to populate memory.")

    st.divider()
    st.caption(
        "**Tier 1** In-context state (LangGraph)\n\n"
        "**Tier 2** JSON store (`data/memory_store.json`)\n\n"
        "**Tier 3** Episodic log (`data/episodic_log.json`)"
    )

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("🏛️ CRAG — Dutch Tax Authority")
st.markdown(
    "Corrective Retrieval-Augmented Generation · "
    "Retrieve → Grade → Rewrite? → Generate → Critic"
)

api_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
ls_configured = bool(os.getenv("LANGSMITH_API_KEY"))

col_api, col_ls = st.columns(2)
col_api.caption(f"Anthropic API: {'✅ configured' if api_configured else '⚠️ not set — running in mock mode'}")
col_ls.caption(f"LangSmith: {'✅ tracing active' if ls_configured else '⚠️ not set — tracing disabled'}")

st.divider()

query = st.text_input(
    "Your Dutch tax question:",
    placeholder="What is the income tax rate for box 1 in 2024?",
)

run_btn = st.button("Ask", type="primary", disabled=not query)

if run_btn and query:
    # ── Pipeline status row ───────────────────────────────────────────────────
    st.markdown("#### Pipeline")
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    ph_retrieve  = p_col1.empty()
    ph_grade     = p_col2.empty()
    ph_generate  = p_col3.empty()
    ph_critic    = p_col4.empty()

    for ph, label in [(ph_retrieve, "Retriever"), (ph_grade, "Grader"),
                      (ph_generate, "Generator"), (ph_critic, "Critic")]:
        ph.info(f"⏳ {label}")

    detail_area = st.empty()

    # ── Run graph with streaming ──────────────────────────────────────────────
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

    final: dict = dict(initial)
    rewrite_rounds: list[str] = []

    for event in graph.stream(initial):
        for node_name, updates in event.items():
            if node_name.startswith("__"):
                continue
            final.update(updates)

            if node_name == "retrieve":
                n = len(updates.get("chunks", []))
                ph_retrieve.success(f"✓ Retriever ({n} chunks)")

            elif node_name == "grade":
                grades = updates.get("grades", [])
                grade_str = " | ".join(grades) if grades else "—"
                ph_grade.success(f"✓ Grader")
                with detail_area.container():
                    st.markdown(f"**Chunk grades:** `{grade_str}`")

            elif node_name == "rewrite":
                new_q = updates.get("query", "")
                rewrite_rounds.append(new_q)
                detail_area.warning(
                    f"🔄 **Query rewritten** (attempt {len(rewrite_rounds)}):\n\n_{new_q}_"
                )
                # Reset retriever/grader indicators for the next loop
                ph_retrieve.info("↻ Retriever")
                ph_grade.info("↻ Grader")

            elif node_name == "generate":
                ph_generate.success("✓ Generator")

            elif node_name == "hallucination_check":
                score = updates.get("hallucination_score", 0.0)
                flagged = updates.get("is_flagged", False)
                if flagged:
                    ph_critic.error(f"✗ Critic ({score:.2f})")
                else:
                    ph_critic.success(f"✓ Critic ({score:.2f})")

    detail_area.empty()

    # ── Results ───────────────────────────────────────────────────────────────
    st.divider()

    score = final.get("hallucination_score", 0.0)
    flagged = final.get("is_flagged", False)

    # Faithfulness score badge
    score_pct = int(score * 100)
    if flagged:
        st.error(f"⚠️ Faithfulness score: **{score:.2f}** ({score_pct}%) — below 0.70 threshold · Safe fallback returned")
    else:
        st.success(f"✓ Faithfulness score: **{score:.2f}** ({score_pct}%) — answer verified")

    # Rewrite history
    if rewrite_rounds:
        st.info(
            f"Query was rewritten **{len(rewrite_rounds)}** time(s).\n\n"
            + "\n".join(f"- Attempt {i+1}: _{q}_" for i, q in enumerate(rewrite_rounds))
        )

    # Answer
    st.markdown("### Answer")
    st.write(final.get("answer", ""))

    # Source chunks
    chunks: list[dict] = final.get("chunks", [])
    grades: list[str] = final.get("grades", [])
    if chunks:
        st.markdown("### Source Chunks")
        for chunk, grade in zip(chunks, grades or [""] * len(chunks)):
            icon = {"RELEVANT": "🟢", "PARTIAL": "🟡", "IRRELEVANT": "🔴"}.get(grade, "⚪")
            with st.expander(f"{icon} [{chunk['article']}] — {grade or 'ungraded'}"):
                st.write(chunk["text"])
                st.caption(f"Source: {chunk['source']} · Year: {chunk['year']}")

    # LangSmith trace link
    if ls_configured:
        ls_project = os.getenv("LANGSMITH_PROJECT", "crag-poc-dutch-tax")
        try:
            from langsmith import Client
            client = Client()
            runs = list(client.list_runs(project_name=ls_project, limit=1, is_root=True))
            if runs:
                run_id = str(runs[0].id)
                # LangSmith URL pattern
                trace_url = (
                    f"https://smith.langchain.com/o/runs/{run_id}"
                    if not hasattr(runs[0], "url") or not runs[0].url
                    else runs[0].url
                )
                st.markdown(f"[View LangSmith trace →]({trace_url})")
            else:
                st.caption(f"Traces available at [smith.langchain.com](https://smith.langchain.com) · project: `{ls_project}`")
        except Exception:
            st.caption(f"Traces available at [smith.langchain.com](https://smith.langchain.com) · project: `{ls_project}`")

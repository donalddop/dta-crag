"""
dta-crag · Streamlit UI

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="dta-crag · Dutch Tax Advisor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    .stApp { background-color: #0f1117; }
    .status-box {
        background: #1a1d27;
        border-left: 3px solid #4A90D9;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin: 0.25rem 0;
        font-family: monospace;
        font-size: 0.85rem;
        color: #aab;
    }
    .score-good  { color: #2ecc71; font-weight: bold; }
    .score-warn  { color: #f39c12; font-weight: bold; }
    .score-bad   { color: #e74c3c; font-weight: bold; }
    .chunk-card {
        background: #1a1d27;
        border: 1px solid #2a2d3a;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin: 0.4rem 0;
    }
    .relevant-tag   { color: #2ecc71; font-weight: bold; font-size: 0.8rem; }
    .irrelevant-tag { color: #e74c3c; font-weight: bold; font-size: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []  # list of {query, answer, score, flagged, chunks, grades}
if "api_key_ok" not in st.session_state:
    st.session_state.api_key_ok = bool(os.environ.get("ANTHROPIC_API_KEY"))

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚖️ dta-crag")
    st.caption("Dutch Tax Advisor · Corrective RAG")
    st.divider()

    api_key_input = st.text_input(
        "Anthropic API key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help="Required. Set in .env file or paste here.",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input
        st.session_state.api_key_ok = True

    st.divider()

    st.markdown("**Pipeline settings**")
    show_chunks = st.toggle("Show retrieved chunks", value=True)
    show_pipeline = st.toggle("Show pipeline trace", value=True)

    st.divider()

    if st.button("🗑️ Clear history"):
        st.session_state.history = []
        st.rerun()

    st.divider()

    # Stats
    try:
        from src.memory import get_stats
        stats = get_stats()
        if stats["total_queries"] > 0:
            st.markdown("**Session stats**")
            st.metric("Queries answered", stats["total_queries"])
            st.metric("Avg faithfulness", f"{stats['avg_faithfulness']:.0%}")
            st.metric("Flag rate", f"{stats['flag_rate']:.0%}")
    except Exception:
        pass

    st.divider()
    st.caption("Sources: Wet IB 2001 · Wet OB 1968 · Wet VPB 1969 · Wet LB 1964 · AWR")

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("⚖️ Dutch Tax Advisor")
st.markdown(
    "Ask a question about Dutch tax law. "
    "The pipeline retrieves relevant legal articles, grades them, "
    "generates an answer, and scores its own faithfulness."
)

# Example questions
with st.expander("💡 Example questions"):
    examples = [
        "Wat is het tarief voor vennootschapsbelasting in 2024?",
        "Hoe werkt de deelnemingsvrijstelling?",
        "Wat zijn de btw-tarieven in Nederland?",
        "Wanneer is er sprake van een aanmerkelijk belang?",
        "Hoe werkt de werkkostenregeling?",
        "Wat is de bijtelling voor een elektrische auto van de zaak?",
        "Hoe wordt box 3 belast na het Kerstarrest?",
        "Wat zijn de regels voor de kleineondernemersregeling?",
    ]
    cols = st.columns(2)
    for i, ex in enumerate(examples):
        if cols[i % 2].button(ex, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill"] = ex

query = st.chat_input(
    "Stel uw belastingvraag… / Ask your tax question…",
)

# Handle prefill from example buttons
if "prefill" in st.session_state:
    query = st.session_state.pop("prefill")

# ── Run pipeline ──────────────────────────────────────────────────────────────

if query:
    if not st.session_state.api_key_ok:
        st.error("Please set your Anthropic API key in the sidebar.")
        st.stop()

    from src.graph import run_pipeline
    from src.memory import cache_get, cache_put, log_query, session_add

    # Check cache
    cached = cache_get(query)
    if cached:
        st.session_state.history.append(
            {
                "query": query,
                "answer": cached["answer"],
                "score": cached["hallucination_score"],
                "flagged": cached["is_flagged"],
                "chunks": [],
                "grades": [],
                "cached": True,
            }
        )
    else:
        status_placeholder = st.empty()

        def _status(msg: str) -> None:
            status_placeholder.markdown(
                f'<div class="status-box">⚙ {msg}</div>', unsafe_allow_html=True
            )

        _status("Retrieving relevant articles…")
        t0 = time.time()

        try:
            state = run_pipeline(query)
        except EnvironmentError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

        elapsed = time.time() - t0
        status_placeholder.empty()

        cache_put(query, state)
        log_query(state)
        session_add(query, state["answer"])

        st.session_state.history.append(
            {
                "query": query,
                "answer": state["answer"],
                "score": state["hallucination_score"],
                "flagged": state["is_flagged"],
                "chunks": state["chunks"],
                "grades": state["grades"],
                "rewrite_count": state["rewrite_count"],
                "elapsed": elapsed,
                "cached": False,
            }
        )

# ── Render history ────────────────────────────────────────────────────────────

for item in reversed(st.session_state.history):
    with st.chat_message("user"):
        st.write(item["query"])

    with st.chat_message("assistant"):
        st.write(item["answer"])

        # Faithfulness badge
        score = item["score"]
        if score >= 0.85:
            badge = f'<span class="score-good">✓ Faithfulness: {score:.0%}</span>'
        elif score >= 0.70:
            badge = f'<span class="score-warn">⚠ Faithfulness: {score:.0%}</span>'
        else:
            badge = f'<span class="score-bad">✗ Faithfulness: {score:.0%} — flagged</span>'

        meta_parts = [badge]
        if item.get("cached"):
            meta_parts.append("📦 cached")
        if item.get("rewrite_count", 0) > 0:
            meta_parts.append(f"↺ {item['rewrite_count']} rewrite(s)")
        if item.get("elapsed"):
            meta_parts.append(f"⏱ {item['elapsed']:.1f}s")

        st.markdown(" · ".join(meta_parts), unsafe_allow_html=True)

        # Pipeline trace
        if show_pipeline and item.get("grades"):
            with st.expander("Pipeline trace", expanded=False):
                relevant = item["grades"].count("RELEVANT")
                total = len(item["grades"])
                st.progress(relevant / total if total else 0, text=f"{relevant}/{total} chunks relevant")

        # Chunks
        if show_chunks and item.get("chunks"):
            with st.expander(f"Retrieved chunks ({len(item['chunks'])})", expanded=False):
                for chunk, grade in zip(item["chunks"], item.get("grades", [])):
                    tag_class = "relevant-tag" if grade == "RELEVANT" else "irrelevant-tag"
                    tag_label = "● RELEVANT" if grade == "RELEVANT" else "● IRRELEVANT"
                    st.markdown(
                        f"""<div class="chunk-card">
                        <strong>{chunk['source']} – {chunk['article']}</strong>
                        &nbsp;&nbsp;<span class="{tag_class}">{tag_label}</span>
                        &nbsp;&nbsp;<span style="color:#666;font-size:0.8rem">sim={chunk['score']:.3f}</span>
                        <br/><em>{chunk['title']}</em>
                        <p style="color:#ccd;margin-top:0.5rem;font-size:0.85rem">{chunk['text'][:400]}…</p>
                        </div>""",
                        unsafe_allow_html=True,
                    )

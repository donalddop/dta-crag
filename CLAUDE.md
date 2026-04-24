# CRAG PoC — Dutch Tax Authority (Belastingdienst)

Corrective Retrieval-Augmented Generation prototype built with LangGraph + Claude.

---

## CRAG Loop Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │               CRAG Loop                     │
                        │                                             │
  User Query ──────────►│  ┌───────────┐    ┌───────────┐            │
                        │  │ RETRIEVER │───►│  GRADER   │            │
                        │  │           │    │ (Sonnet)  │            │
                        │  └───────────┘    └─────┬─────┘            │
                        │        ▲                │                  │
                        │        │                │ majority          │
                        │        │           IRRELEVANT?              │
                        │        │           & rewrites < 2?          │
                        │        │          yes │       │ no          │
                        │        │    ┌─────────┘       │            │
                        │        │    ▼                 ▼            │
                        │        │  ┌───────────┐  ┌───────────┐    │
                        │        └──│  REWRITER │  │ GENERATOR │    │
                        │           │ (Sonnet)  │  │  (Opus)   │    │
                        │           └───────────┘  └─────┬─────┘    │
                        │                                │           │
                        │                          ┌─────▼─────┐    │
                        │                          │  CRITIC   │    │
                        │                          │ (Sonnet)  │    │
                        │                          └─────┬─────┘    │
                        └────────────────────────────────┼──────────┘
                                                         │
                                score ≥ 0.70 ◄──────────┤
                                     │                   │ score < 0.70
                                     ▼                   ▼
                               Final Answer        Safe Fallback
                                                 + Episodic Log
```

---

## Agent Roles and Responsibilities

| Agent | Model | Role |
|---|---|---|
| **Retriever** | — (mock / vector store) | Fetches relevant Dutch tax law chunks for the current query |
| **Grader** | claude-sonnet-4-6 | Classifies each chunk as RELEVANT / PARTIAL / IRRELEVANT |
| **Rewriter** | claude-sonnet-4-6 | Rewrites vague queries using proper Dutch tax terminology; max 2 attempts |
| **Generator** | claude-opus-4-7 | Synthesises a grounded answer citing article numbers; refuses out-of-domain questions |
| **Critic** | claude-sonnet-4-6 | Scores answer faithfulness 0.0–1.0; flags answers below 0.70 threshold |

---

## Domain Rules

All agents observe these rules (enforced in `src/prompts.py`):

1. **Always cite article numbers** — e.g. "Wet IB 2001, Art. 2.10"
2. **Never answer outside Dutch tax law scope** — out-of-domain queries trigger `DOMAIN_VIOLATION` sentinel
3. **State the applicable tax year** when quoting rates or thresholds
4. **Distinguish tax boxes** (box 1 / box 2 / box 3) where relevant
5. **Faithfulness threshold = 0.70** — answers scoring below this are replaced with the safe fallback

---

## Memory Tiers

| Tier | Mechanism | Location | What is stored |
|---|---|---|---|
| **1 — In-context** | LangGraph `CRAGState` dict | Runtime only | `query`, `chunks`, `grades`, `rewrite_count`, `answer`, `hallucination_score`, `is_flagged` |
| **2 — Persistent store** | JSON file | `data/memory_store.json` | Every completed run: `{query, answer, grade_summary, is_flagged, timestamp}`. Top-3 recent successful runs are injected as few-shot examples on new queries. |
| **3 — Episodic log** | JSON file | `data/episodic_log.json` | Correction entries when `hallucination_score < 0.70`: `{query, flagged_answer, score, timestamp, correction_note}` |

---

## How to Run

### Prerequisites

```bash
cd crag_poc
cp .env.example .env          # fill in your API keys
uv venv --python 3.11 .venv
uv pip install -r requirements.txt
```

### Streamlit UI

```bash
.venv/bin/streamlit run app.py
# Opens at http://localhost:8501
```

### Headless Demo (3 scenarios)

```bash
.venv/bin/python demo.py
```

Expected scenario outcomes:

| # | Query | Expected behaviour |
|---|---|---|
| 1 | "What is the income tax rate for box 1 in 2024?" | RELEVANT chunks → generate → Critic PASSES |
| 2 | "belasting op winst" | IRRELEVANT → rewrite → retry → generate → Critic PASSES |
| 3 | Pizza recipe question | Critic FAILS (score < 0.70) → safe fallback returned |

---

## How to View LangSmith Traces

1. Set `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT=crag-poc-dutch-tax` in `.env`
2. Run any query via `app.py` or `demo.py`
3. Visit [https://smith.langchain.com](https://smith.langchain.com) → select project **crag-poc-dutch-tax**
4. Each graph run appears as a root trace; expand it to see individual node runs (retrieve → grade → rewrite? → generate → hallucination_check)
5. The Streamlit UI shows a "View LangSmith trace →" link after each run when the key is configured

---

## File Map

```
crag_poc/
├── src/
│   ├── graph.py        LangGraph state machine + CRAGState TypedDict
│   ├── nodes.py        All agent node functions (+ mock fallbacks)
│   ├── memory.py       Tier-2 JSON store and Tier-3 episodic log
│   └── prompts.py      All LLM prompt templates (single source of truth)
├── data/
│   ├── memory_store.json   Tier-2 persistent Q&A store
│   └── episodic_log.json   Tier-3 correction log
├── .claude/skills/     Agent capability cards (used by Claude Code)
├── app.py              Streamlit UI
├── demo.py             Headless 3-scenario demo
├── requirements.txt
├── pyproject.toml
└── .env.example
```

# CRAG PoC — Dutch Tax Authority

Corrective Retrieval-Augmented Generation prototype built with **LangGraph** and **Claude**. Submitted as an AI engineering assessment deliverable for the Belastingdienst.

---

## What it does

A user asks a Dutch tax question. Four agents collaborate to produce a verified answer:

```
User question
     │
     ▼
┌─────────────┐
│  Retriever  │  Fetches relevant Dutch tax law chunks
└──────┬──────┘
       ▼
┌─────────────┐
│   Grader    │  Classifies each chunk: RELEVANT / PARTIAL / IRRELEVANT
└──────┬──────┘
       │
  majority IRRELEVANT          else
  & rewrites < 2  ─────────────────────────────────────────────┐
       │                                                        ▼
       ▼                                               ┌─────────────────┐
┌─────────────┐                                        │    Generator    │
│   Rewriter  │ ── rewrites query ──► Retriever again  │  (answer draft) │
└─────────────┘                                        └────────┬────────┘
                                                                ▼
                                                       ┌─────────────────┐
                                                       │     Critic      │
                                                       │ faithfulness    │
                                                       │ score 0.0–1.0   │
                                                       └────────┬────────┘
                                                 score ≥ 0.70   │  score < 0.70
                                                       ▼        │        ▼
                                                 Final answer   │   Safe fallback
                                                                │  + episodic log
```

**Domain rules enforced across all agents:**
- Answers must cite article numbers (e.g. *Wet IB 2001, Art. 2.10*)
- Questions outside Dutch tax law scope are refused
- Answers scoring below 0.70 faithfulness are replaced with a safe fallback

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| `uv` | ≥ 0.9 | Python package manager — already at `~/.local/bin/uv` |
| Python | 3.11 | Managed by uv |
| LLM backend | — | See [Configuration](#configuration) below |

---

## Installation

```bash
cd crag_poc
uv venv --python 3.11 .venv
uv pip install -r requirements.txt
cp .env.example .env
# Edit .env — see Configuration below
```

---

## Configuration

All settings live in `crag_poc/.env`. Two LLM backend options:

### Option A — Direct Anthropic API
Requires API credits at [console.anthropic.com](https://console.anthropic.com).

```env
ANTHROPIC_API_KEY=sk-ant-...
```

### Option B — Hermes gateway (uses your claude_code OAuth / Pro subscription)
No API credits needed. Requires [Hermes](https://github.com/openclawai/hermes) to be installed.

```env
# leave ANTHROPIC_API_KEY blank or commented out
HERMES_API_KEY=crag-poc-local
HERMES_BASE_URL=http://localhost:8642/v1
```

Then start the gateway in a separate terminal before running the demo:
```bash
hermes gateway run
```

### LangSmith tracing (optional)
Sign up at [smith.langchain.com](https://smith.langchain.com) → Settings → API Keys.

```env
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=crag-poc-dutch-tax
LANGCHAIN_TRACING_V2=true
```

---

## Running

### Headless demo — 3 canonical scenarios

```bash
cd crag_poc
.venv/bin/python demo.py
```

| # | Query | Expected outcome |
|---|---|---|
| 1 | *"What is the income tax rate for box 1 in 2024?"* | Retrieves RELEVANT chunks → generates → Critic PASSES |
| 2 | *"belasting op winst"* (vague) | Grades IRRELEVANT → rewrites query → retries → generates → Critic PASSES |
| 3 | Pizza recipe question (out-of-domain) | Critic FAILS (score < 0.70) → safe fallback returned |

> **No credentials?** The demo runs in full mock mode — all three scenarios still execute correctly with deterministic stubs.

### Streamlit UI

```bash
cd crag_poc
.venv/bin/streamlit run app.py
# Opens at http://localhost:8501
```

Features:
- Type any Dutch tax question and watch each pipeline step light up in real time
- Green/red hallucination score badge per answer
- Expandable source chunks with per-chunk grade indicator
- Sidebar showing the last 3 queries from persistent memory
- "View LangSmith trace →" link when tracing is configured

---

## File descriptions

```
crag_poc/
│
├── src/
│   ├── graph.py          LangGraph state machine
│   │                     • CRAGState TypedDict (query, chunks, grades,
│   │                       rewrite_count, answer, hallucination_score, is_flagged)
│   │                     • _branch() routing: majority IRRELEVANT → rewrite; else generate
│   │                     • build_graph() → compiled StateGraph
│   │                     • run_query(query) → CRAGState convenience wrapper
│   │
│   ├── nodes.py          All five agent node functions
│   │                     • retrieve_node   — keyword mock over 6 Dutch tax law chunks
│   │                     • grade_node      — RELEVANT/PARTIAL/IRRELEVANT per chunk
│   │                     • rewrite_node    — Dutch tax terminology query improvement
│   │                     • generate_node   — grounded answer with article citations
│   │                     • hallucination_check_node — faithfulness score; safe fallback
│   │                     • _llm_call()     — 3-way backend: Anthropic → Hermes → mock
│   │
│   ├── memory.py         Three-tier memory layer
│   │                     • Tier 1: CRAGState dict (in-context, nothing extra here)
│   │                     • Tier 2: save_run_to_memory() / get_recent_runs() / build_few_shot_section()
│   │                     • Tier 3: log_correction() → episodic_log.json
│   │
│   └── prompts.py        Single source of truth for all LLM prompt strings
│                         • GRADE, GENERATE, REWRITE, HALLUCINATION prompts
│                         • SAFE_FALLBACK_RESPONSE (bilingual NL/EN)
│
├── data/
│   ├── memory_store.json  Tier-2 persistent Q&A history (committed empty; populated at runtime)
│   └── episodic_log.json  Tier-3 correction log for flagged answers (committed empty)
│
├── .claude/
│   └── skills/
│       ├── retriever.md   Agent capability card: retrieval contract and upgrade path
│       ├── grader.md      Agent capability card: grading rubric and branch trigger logic
│       ├── generator.md   Agent capability card: domain rules and citation requirements
│       └── critic.md      Agent capability card: faithfulness scoring and memory side-effects
│
├── app.py                 Streamlit demo UI (streaming pipeline status, chunk viewer)
├── demo.py                Headless 3-scenario runner (works without credentials)
│
├── CLAUDE.md              Full project spec: ASCII diagram, agent roles, run instructions
├── BUILDLOG.md            Session build log: design decisions and rationale
├── README.md              This file
│
├── requirements.txt       pip-compatible dependency list
├── pyproject.toml         uv-compatible project config
└── .env.example           Environment variable template
```

---

## Agent models

| Agent | Model | Why |
|---|---|---|
| Grader | `claude-sonnet-4-6` | Fast binary classification; low latency per chunk |
| Rewriter | `claude-sonnet-4-6` | Query reformulation; short output |
| Generator | `claude-opus-4-7` | Best reasoning for grounded synthesis (falls back to Sonnet via Hermes) |
| Critic | `claude-sonnet-4-6` | Faithful scoring; short numeric output |

---

## Memory tiers

| Tier | Where | What |
|---|---|---|
| 1 — In-context | `CRAGState` dict | Live query, chunks, grades, rewrite count |
| 2 — Persistent store | `data/memory_store.json` | Every completed run; top-3 injected as few-shot examples on next query |
| 3 — Episodic log | `data/episodic_log.json` | Flagged answers (score < 0.70) with correction notes |

---

## LangSmith traces

When `LANGCHAIN_TRACING_V2=true` and `LANGSMITH_API_KEY` are set, every graph run is traced. Navigate to [smith.langchain.com](https://smith.langchain.com) → project **crag-poc-dutch-tax** to see the full node waterfall for each run.

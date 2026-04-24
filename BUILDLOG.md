# Build Log — CRAG PoC for the Dutch Tax Authority

Chronological record of the design session: user prompts summarised, key decisions noted, and the reasoning behind each choice.

---

## Session Overview

**Goal:** Build a LangGraph-based Corrective RAG (CRAG) prototype as an AI engineering assessment deliverable for the Dutch Tax Authority (Belastingdienst).

**Demonstrates:**
- Multi-agent CRAG loop with corrective retrieval
- Agents auditing each other's work (Grader audits Retriever, Critic audits Generator)
- Three-tier agent memory (in-context state, external JSON store, episodic correction log)
- Structured agent governance via CLAUDE.md and `.claude/skills/`

---

## Phase 0 — Orient

**User prompt:** Read this entire spec and tell me what's already in the directory; check if langgraph, langchain, anthropic, streamlit, and langsmith are installed.

**Findings:**
- `/home/donald/repos/dta-crag/` was completely empty — clean slate
- `pip` not available on system Python; `uv` (v0.9.18) was installed at `~/.local/bin/uv`
- Python 3.11.14 and 3.12.12 managed by uv
- None of the required packages were installed

**Decision:** Use `uv` for venv creation and package installation (faster than pip, already present). Create `pyproject.toml` alongside `requirements.txt` so both `uv sync` and `pip install -r` workflows are supported.

**User confirmation:** "ok go"

---

## Phase 1 — Scaffold

**Action:** Created the full project structure under `crag_poc/` with all files wired end-to-end in mock mode (no real LLM calls required).

**Files created:**
- `src/prompts.py` — single source of truth for all prompt strings
- `src/memory.py` — three-tier memory (in-context state dict; JSON store; episodic log)
- `src/nodes.py` — all five agent nodes with `@traceable` decorators and deterministic mock fallbacks
- `src/graph.py` — `StateGraph` with `CRAGState` TypedDict; `_branch()` routing logic; `build_graph()` factory
- `app.py` — Streamlit UI with live pipeline status, chunk viewer, hallucination score badge
- `demo.py` — headless 3-scenario runner
- `CLAUDE.md` — ASCII loop diagram, agent roles, domain rules, memory tiers, run instructions
- `.claude/skills/{retriever,grader,generator,critic}.md` — agent capability cards
- `data/memory_store.json`, `data/episodic_log.json` — empty stores
- `requirements.txt`, `pyproject.toml`, `.env.example`

**Key design decisions:**
- `total=False` TypedDict allows partial state updates from each node; LangGraph merges them
- Mock retrieval uses keyword matching against six hardcoded Dutch tax law chunks (Wet IB 2001, Wet OB 1968, Wet DB 1965, Wet VPB 1969)
- Mock grader requires *specific* tax terms (box numbers, article keywords) so a vague query like "belasting op winst" correctly triggers a rewrite in mock mode
- Hallucination checker evaluates against `original_query` (not the rewritten one) so an out-of-domain pizza question still fails even after its query gets rewritten with tax keywords

**Smoke test results:**
```
Scenario 1  Good Retrieval       0 rewrites  score=0.90  PASSED
Scenario 2  Rewrite Trigger      1 rewrite   score=0.90  PASSED
Scenario 3  Out-of-Domain        1 rewrite   score=0.20  FLAGGED → safe fallback
```

Both JSON stores updated correctly; `episodic_log.json` captured the pizza query correction.

---

## Phase 2 — LangSmith Setup

**User prompt:** Added Anthropic and LangSmith API keys to `.env`; asked how to set up LangSmith tracing.

**Findings:**
- User had placed the real API key in `.env.example` (the template file) instead of `.env`. `.env.example` was restored to placeholder values.
- `.env` already existed with the correct key.
- LangSmith setup: sign up at smith.langchain.com → Settings → API Keys → create key → add to `.env` as `LANGSMITH_API_KEY`.
- `LANGCHAIN_TRACING_V2=true` was already in the `.env` template to auto-enable tracing.
- LangSmith 403 on first run — API key returned 404 on all endpoints (likely unactivated workspace). Tracing temporarily disabled (`LANGCHAIN_TRACING_V2=false`) to unblock the demo.

---

## Phase 3 — Hermes / OpenClaw Research

**User prompt:** "My credit is too low for the Anthropic API, can I use my Pro subscription instead?" then "Can I also use an openclaw or hermes agent connected to Anthropic instead?"

**Research findings:**
- **OpenClaw** was an open-source agent framework, renamed to **Hermes** in early 2026 (confirmed by `hermes claw migrate` subcommand and `/home/donald/.hermes/migration/openclaw/` directory)
- `hermes` was already installed at `~/.local/bin/hermes` (v0.8.0, 2026.4.8)
- Hermes was already configured with `claude-sonnet-4-6` via `claude_code` OAuth credential
- Hermes exposes a full **OpenAI-compatible API server** at `http://localhost:8642/v1`:
  - `POST /v1/chat/completions`
  - `GET /v1/models`
  - `GET /health`
- Enabled the API server by adding to `~/.hermes/.env`:
  ```
  API_SERVER_ENABLED=true
  API_SERVER_KEY=crag-poc-local
  API_SERVER_PORT=8642
  ```

**Code changes:**
- Added `openai>=1.0` to `requirements.txt`
- Rewrote LLM dispatch in `src/nodes.py` as a clean three-way backend selector:

  | Priority | Condition | Backend |
  |---|---|---|
  | 1 | `ANTHROPIC_API_KEY` set | Direct Anthropic SDK |
  | 2 | `HERMES_API_KEY` set | Hermes OpenAI-compat API |
  | 3 | Neither | Deterministic mock |

- All four LLM-calling nodes (grade, rewrite, generate, hallucination_check) now call `_llm_call()` instead of directly instantiating SDK clients.

**Caveat:** Hermes routes all calls through its configured model (`claude-sonnet-4-6`) regardless of the `model` field in the request, so the Generator will also use Sonnet rather than Opus 4.7 when going through Hermes.

**To use Hermes backend:**
1. In a terminal: `hermes gateway run`
2. In `crag_poc/.env`: comment out `ANTHROPIC_API_KEY`, uncomment `HERMES_API_KEY` and `HERMES_BASE_URL`

---

## Phase 4 — Paperclip AI Research (Not Used)

**User prompt:** "Now what about making this a paperclip AI company? Also research online."

**Research findings:**
- **Paperclip** (paperclip.ing, MIT licensed) is an open-source multi-agent orchestration platform — an "operating system for an AI company" with departments, budgets, token limits, and approval gates
- It exposes a heartbeat protocol; each "agent" can be a Claude Code session, Python script, or LangGraph app
- `paperclip-mcp` Python package wraps its REST API as an MCP server

**Decision:** Not used. LangGraph already handles CRAG pipeline orchestration cleanly. Paperclip would add value for managing *teams* of many independent agents toward shared business goals, which is out of scope for a single-pipeline PoC.

---

## Current State

**Backend:** Hermes gateway (pending `hermes gateway run` in a separate terminal — being debugged)

**What works:**
- Full CRAG graph runs end-to-end in mock mode: `python demo.py`
- Streamlit UI: `streamlit run app.py`
- All three memory tiers are operational
- LangSmith tracing is wired (pending valid API key)

**What's pending:**
- `hermes gateway run` errors — debugging deferred
- LangSmith API key 403 — account activation may be needed
- Real LLM calls (blocked on either API credits or Hermes gateway)

---

## Architecture Reference

```
retrieve → grade → [branch] → rewrite ──┐
                        │               └──→ retrieve (loop, max 2 rewrites)
                        └──────────────────→ generate → hallucination_check → END
```

| Node | Model | Role |
|---|---|---|
| retrieve | — | Keyword mock / vector store |
| grade | claude-sonnet-4-6 | RELEVANT / PARTIAL / IRRELEVANT per chunk |
| rewrite | claude-sonnet-4-6 | Query improvement using Dutch tax terminology |
| generate | claude-opus-4-7 (Sonnet via Hermes) | Grounded answer with article citations |
| hallucination_check | claude-sonnet-4-6 | Faithfulness score 0.0–1.0; safe fallback if < 0.70 |

---

## File Map

```
crag_poc/
├── src/
│   ├── graph.py        LangGraph CRAGState + build_graph()
│   ├── nodes.py        Five agent nodes; _llm_call() with 3-way backend
│   ├── memory.py       Tier-2 JSON store + Tier-3 episodic log
│   └── prompts.py      All prompt templates (single source of truth)
├── data/
│   ├── memory_store.json   Tier-2 Q&A history
│   └── episodic_log.json   Tier-3 correction log
├── .claude/skills/     Agent capability cards
├── app.py              Streamlit UI
├── demo.py             Headless demo (3 scenarios)
├── CLAUDE.md           Project docs + ASCII diagram
├── BUILDLOG.md         This file
├── requirements.txt
├── pyproject.toml
└── .env.example
```

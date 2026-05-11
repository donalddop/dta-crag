# CLAUDE.md — dta-crag System Documentation

This file describes the architecture, agent roles, routing rules, and memory layers of the dta-crag multi-agent CRAG system.

---

## System overview

**dta-crag** is a Corrective Retrieval-Augmented Generation (CRAG) system for Dutch tax law Q&A. It combines four collaborating agent types in a LangGraph state machine, with a Supervisor that routes queries before the pipeline runs.

```
User query
    │
    ▼
┌──────────────┐
│  SUPERVISOR  │  Classifies query: TAX / GENERAL / HARMFUL
└──────┬───────┘
       │ TAX                    GENERAL / HARMFUL
       │                              │
       ▼                              ▼
┌──────────────┐              ┌───────────────┐
│  RETRIEVER   │              │  Safe refusal │
└──────┬───────┘              └───────────────┘
       │
       ▼
┌──────────────┐
│    GRADER    │  Labels each chunk RELEVANT / IRRELEVANT
└──────┬───────┘
       │
  majority        all budget
  irrelevant?  ←  exhausted?
       │ yes            │ no → rewrite limit reached
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│   REWRITER   │  │  GENERATOR   │
└──────┬───────┘  └──────┬───────┘
       │                  │
       └──→ RETRIEVER      ▼
                   ┌──────────────┐
                   │    CRITIC    │  Scores faithfulness; flags if < 0.70
                   └──────┬───────┘
                          │
                          ▼
                      Final answer
```

---

## Agent roles

### Supervisor (`src/supervisor.py`)
- **Input**: raw user query
- **Action**: calls Claude to classify as `TAX`, `GENERAL`, or `HARMFUL`
- **Output**: routes to the CRAG pipeline or returns a safe refusal directly
- **Logs as**: `[SUPERVISOR]`

### Retriever (`src/retriever.py`, node: `node_retrieve`)
- **Input**: current query string (may have been rewritten)
- **Action**: embeds the query with `paraphrase-multilingual-MiniLM-L12-v2` and queries the Chroma vector store for top-5 chunks
- **Output**: list of chunk dicts (`id`, `source`, `article`, `title`, `text`, `score`)
- **Logs as**: `[RETRIEVER]`

### Grader (`src/nodes.py`, node: `node_grade`)
- **Input**: query + retrieved chunks
- **Action**: calls Claude once per chunk (in parallel threads) to label each as `RELEVANT` or `IRRELEVANT`
- **Routing decision**: if majority irrelevant AND rewrite budget remains → rewrite; otherwise → generate
- **Logs as**: `[GRADER]`

### Rewriter (`src/nodes.py`, node: `node_rewrite`)
- **Input**: current (possibly ambiguous) query
- **Action**: calls Claude to reformulate the query for better retrieval; loops back to Retriever
- **Budget**: max 2 rewrites per query (`MAX_REWRITES = 2`)
- **Logs as**: `[REWRITER]`

### Generator (`src/nodes.py`, node: `node_generate`)
- **Input**: original query + relevant chunks
- **Action**: calls Claude to produce a grounded Dutch-language answer with article citations
- **Context policy**: uses only RELEVANT chunks; falls back to all chunks if none are relevant
- **Logs as**: `[GENERATOR]`

### Critic (`src/nodes.py`, node: `node_critique`)
- **Input**: generated answer + source chunks
- **Action**: calls Claude to score faithfulness (0.0–1.0); if < 0.70, substitutes a bilingual safe fallback
- **Logs as**: `[CRITIC]`

---

## Routing rules

| Condition | Route |
|-----------|-------|
| Query classified `TAX` | → CRAG pipeline |
| Query classified `GENERAL` | → off-topic refusal (no pipeline) |
| Query classified `HARMFUL` | → fraud/evasion refusal (no pipeline) |
| Majority chunks `IRRELEVANT` AND rewrites < 2 | grade → rewrite → retrieve |
| Majority chunks `IRRELEVANT` AND rewrites = 2 | grade → generate (budget exhausted) |
| Majority chunks `RELEVANT` | grade → generate |
| Faithfulness score ≥ 0.70 | return answer as-is |
| Faithfulness score < 0.70 | replace answer with safe fallback |

---

## Memory layers

Three-tier memory is implemented in `src/memory.py`:

| Tier | Type | Persistence | Purpose |
|------|------|-------------|---------|
| 1 | Semantic cache | In-memory (process lifetime) | Skip duplicate LLM calls for identical queries |
| 2 | Session context | In-memory (process lifetime) | Last N exchanges available for follow-up context |
| 3 | Episodic log | `data/episodic_log.json` | Persistent audit trail of all queries and outcomes |

The episodic log records: timestamp, original query, final query, rewrite count, chunk counts, faithfulness score, and whether the answer was flagged.

---

## State schema (`CRAGState`)

Defined in `src/nodes.py`:

```python
class CRAGState(TypedDict):
    query:              str          # Current query (may be rewritten)
    original_query:     str          # Never changes — used by Generator
    chunks:             list[dict]   # Retrieved chunks
    grades:             list[str]    # "RELEVANT" | "IRRELEVANT" per chunk
    rewrite_count:      int          # Number of rewrites so far
    answer:             str          # Final answer (or fallback)
    hallucination_score: float       # Critic score 0.0–1.0
    is_flagged:         bool         # True if score < 0.70
```

---

## Key configuration

| Setting | Location | Default |
|---------|----------|---------|
| Retrieval k | `src/nodes.py` `RETRIEVAL_K` | 5 |
| Max rewrites | `src/nodes.py` `MAX_REWRITES` | 2 |
| Faithfulness threshold | `src/nodes.py` `FAITHFULNESS_THRESHOLD` | 0.70 |
| Embedding model | `src/retriever.py` `EMBED_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` |
| LLM model | `src/nodes.py` `_call()` | `claude-sonnet-4-6` |
| Chroma path | `src/retriever.py` `CHROMA_DIR` | `data/chroma_db/` |
| Episodic log | `src/memory.py` | `data/episodic_log.json` |

---

## Skill files

See `.claude/skills/` for agent-specific governance:

- [`retriever.md`](.claude/skills/retriever.md) — corpus coverage, API, index management
- [`tax_expert.md`](.claude/skills/tax_expert.md) — citation rules, faithfulness threshold, refusal policy

---

## Quick start

```bash
# Install dependencies
uv sync

# Set API key
cp .env.example .env
# Edit .env → ANTHROPIC_API_KEY=sk-ant-...

# Run a single query (CLI)
uv run python main.py "Wat is het btw-tarief voor boeken?"

# Run the three-scenario demo
uv run python demo.py

# Run the Streamlit UI
uv run streamlit run app.py

# Run tests
uv run pytest
```

# dta-crag · Dutch Tax Advisor

A working Corrective RAG (CRAG) prototype for Dutch tax law Q&A, built with LangGraph, sentence-transformers, Chroma, and the Anthropic API.

## Pipeline

```
retrieve → grade → [rewrite → retrieve]* → generate → critique → answer
```

1. **Retrieve** — vector search over Dutch tax law corpus (sentence-transformers + Chroma)
2. **Grade** — LLM grades each chunk as RELEVANT or IRRELEVANT
3. **Rewrite** (conditional) — if majority irrelevant, rewrite the query and retry (max 2×)
4. **Generate** — answer from relevant chunks using Claude
5. **Critique** — faithfulness score (0–1); below 0.70 triggers a safe fallback

## Sources

| Law | Coverage |
|-----|----------|
| Wet IB 2001 | Income tax: box 1/2/3, deductions, own home |
| Wet OB 1968 | VAT: rates, exemptions, input tax deduction, KOR |
| Wet VPB 1969 | Corporate tax: rates, participation exemption, fiscal unity, innovation box |
| Wet LB 1964 | Payroll tax: WKR, company car, brackets |
| AWR | Reassessment, penalties |
| Successiewet | Inheritance and gift tax |

## Quick start

```bash
# 1. Install dependencies (uv recommended)
uv sync

# 2. Set your Anthropic API key
cp .env.example .env
# edit .env and add ANTHROPIC_API_KEY=sk-ant-...

# 3. Run a single query
uv run python main.py "Wat is BTW?"

# 4. Run the three-scenario demo
uv run python demo.py

# 5. Or launch the Streamlit UI
uv run streamlit run app.py
```

> **Alternative (pip):** `pip install -r requirements.txt`, then use `python` instead of `uv run python`.

## Project structure

```
dta-crag/
├── src/
│   ├── supervisor.py      # Supervisor agent — query classification & routing
│   ├── nodes.py           # LangGraph nodes: retrieve, grade, rewrite, generate, critique
│   ├── graph.py           # LangGraph state machine
│   ├── retriever.py       # Chroma + sentence-transformers vector store
│   ├── corpus.py          # 30+ Dutch tax law chunks
│   ├── prompts.py         # All prompt templates (NL)
│   ├── memory.py          # 3-tier memory (cache / session / episodic log)
│   └── logging_config.py  # Colored agent logging
├── .claude/
│   └── skills/
│       ├── retriever.md   # Corpus coverage, API, index management
│       └── tax_expert.md  # Citation rules, faithfulness threshold, refusal policy
├── data/
│   ├── chroma_db/         # Vector index (auto-created on first run)
│   └── episodic_log.json
├── tests/                 # Pytest suite (94 tests)
├── CLAUDE.md              # Architecture, agent roles, routing rules, memory layers
├── main.py                # CLI: uv run python main.py "..."
├── demo.py                # Three-scenario headless demo
├── app.py                 # Streamlit UI
├── pyproject.toml
└── .env.example
```

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Required. Your Anthropic API key. |
| `LANGCHAIN_TRACING_V2` | Optional. Set to `true` to enable LangSmith tracing. |
| `LANGCHAIN_API_KEY` | Required if tracing is enabled. |

## Notes

- The Chroma index is built on first run and persisted to `data/chroma_db/`. Subsequent startups are fast.
- To update the corpus, edit `src/corpus.py` and run `python -c "from src.retriever import reset_index; reset_index()"`.
- The embedding model (`paraphrase-multilingual-MiniLM-L12-v2`) is downloaded automatically on first run (~120 MB).

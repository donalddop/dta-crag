# Retriever Agent

## Role
Fetches relevant Dutch tax law document chunks for the current query.

## Input (from CRAGState)
- `query` — the current search query (may have been rewritten by the Rewriter)

## Output (state update)
- `chunks` — list of `{id, article, text, source, year}` dicts

## Current implementation
Mock keyword-based retrieval over a hardcoded corpus of six chunks covering:
- **Wet IB 2001, Art. 2.10** — box 1 income tax rates 2024
- **Wet IB 2001, Art. 4.6** — box 2 substantial interest rates 2024
- **Wet IB 2001, Art. 5.2** — box 3 capital savings tax 2024
- **Wet OB 1968, Art. 9** — VAT rates 2024
- **Wet DB 1965, Art. 1** — dividend withholding tax 2024
- **Wet VPB 1969, Art. 22** — corporate tax rates 2024

## Upgrade path
Replace `_mock_retrieve()` in `src/nodes.py` with a real vector store:
```python
# e.g. using pgvector, Pinecone, or Chroma
results = vector_store.similarity_search(query, k=5)
```

## Contract
- Always returns at least one chunk (even for unrecognised queries)
- For unrecognised queries returns `chunk_001` as a fallback; Grader will classify it IRRELEVANT

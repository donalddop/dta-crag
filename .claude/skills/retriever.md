# Skill: Retriever

## Role
The Retriever agent queries the FAISS-like vector store and returns the top-k most semantically similar chunks for a given query.

## Implementation
- **File**: `src/retriever.py`
- **Vector store**: Chroma (persistent, stored in `data/chroma_db/`)
- **Embedding model**: `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers, ~120 MB, auto-downloaded on first run)
- **Distance metric**: Cosine similarity

## Corpus
The corpus covers four Dutch tax laws and supporting regulation:

| ID prefix | Source | Topics |
|-----------|--------|--------|
| `ib_*`    | Wet IB 2001 | Income tax: box 1/2/3, deductions, own home, aanmerkelijk belang |
| `ob_*`    | Wet OB 1968 | VAT: rates (21%/9%/0%), exemptions, input tax, KOR |
| `vpb_*`   | Wet VPB 1969 | Corporate tax: rates, participation exemption, fiscal unity, innovation box |
| `lb_*`    | Wet LB 1964 | Payroll tax: WKR, company car bijtelling, brackets |
| `awr_*`   | AWR | Reassessment (navordering), penalties |
| `*`       | Successiewet 1956, BPM, Dividendbelasting | Inheritance, gift tax, vehicle tax |

## Public API

```python
from src.retriever import retrieve, reset_index

chunks = retrieve(query="Wat is het btw-tarief?", k=5)
```

Each returned chunk is a dict:

```python
{
    "id":      "ob_9",
    "source":  "Wet OB 1968",
    "article": "Art. 9",
    "title":   "Tarieven omzetbelasting",
    "text":    "De belasting bedraagt 21% (algemeen tarief)…",
    "score":   0.8731,   # cosine similarity, higher = more relevant
}
```

## Default behaviour
- `k=5` chunks returned per query
- First call builds and persists the Chroma index (slow, ~5–15 s)
- Subsequent calls load from disk (fast, <1 s)

## Rebuilding the index
Run after editing `src/corpus.py`:

```bash
uv run python -c "from src.retriever import reset_index; reset_index()"
```

## Routing context
The Retriever is always the first node after the Supervisor routes a query to the TAX_AGENT. After retrieval, control passes to the Grader.

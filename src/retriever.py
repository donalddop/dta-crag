"""
Vector retriever: sentence-transformers embeddings + Chroma vector store.

The collection is built once on first use and persisted to disk.
Subsequent calls load from disk (fast).
"""

from __future__ import annotations

import os
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .corpus import get_all_chunks, get_chunk_texts, get_chunk_ids

# ── Configuration ─────────────────────────────────────────────────────────────

# Multilingual model — handles Dutch and English queries equally well
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

COLLECTION_NAME = "dta_crag_nl"

# Persist alongside the project data directory
_HERE = Path(__file__).parent.parent
CHROMA_DIR = str(_HERE / "data" / "chroma_db")

# ── Module-level singletons (lazy init) ───────────────────────────────────────

_embedder: SentenceTransformer | None = None
_collection: chromadb.Collection | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )

    existing = {c.name for c in client.list_collections()}

    if COLLECTION_NAME in existing:
        _collection = client.get_collection(COLLECTION_NAME)
        return _collection

    # First run: build the index
    _collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    _index_corpus(_collection)
    return _collection


def _index_corpus(collection: chromadb.Collection) -> None:
    """Embed the corpus and upsert into Chroma."""
    embedder = _get_embedder()
    chunks = get_all_chunks()
    texts = get_chunk_texts()
    ids = get_chunk_ids()

    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()

    metadatas = [
        {
            "source": c["source"],
            "article": c["article"],
            "title": c["title"],
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Retrieve the top-k most relevant corpus chunks for a query.

    Returns a list of dicts with keys: id, source, article, title, text, score.
    """
    embedder = _get_embedder()
    collection = _get_collection()

    query_embedding = embedder.encode([query], show_progress_bar=False).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks_out = []
    for i in range(len(results["ids"][0])):
        chunk_id = results["ids"][0][i]
        meta = results["metadatas"][0][i]
        doc = results["documents"][0][i]
        distance = results["distances"][0][i]
        similarity = 1.0 - distance  # cosine distance → similarity

        # Extract the plain text (strip the "source article – title\n\n" prefix)
        text = doc.split("\n\n", 1)[1] if "\n\n" in doc else doc

        chunks_out.append(
            {
                "id": chunk_id,
                "source": meta["source"],
                "article": meta["article"],
                "title": meta["title"],
                "text": text,
                "score": round(similarity, 4),
            }
        )

    return chunks_out


def reset_index() -> None:
    """Delete and rebuild the Chroma collection (useful after corpus updates)."""
    global _collection
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    _get_collection()  # rebuild

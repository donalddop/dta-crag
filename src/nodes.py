"""All agent node functions.

Each node is a plain function (state: dict) -> dict that returns only the fields
it wants to update.  Every node is wrapped with @traceable for LangSmith tracing.

Backend priority (checked in order):
  1. Direct Anthropic API  — set ANTHROPIC_API_KEY in crag_poc/.env
  2. Hermes gateway        — start `hermes gateway run`, set HERMES_API_KEY in crag_poc/.env
  3. Mock mode             — deterministic stubs, no credentials required
"""

import os
import re
from typing import Any

import anthropic
from langsmith import traceable

from .prompts import (
    GRADE_SYSTEM_PROMPT,
    GRADE_USER_PROMPT,
    GENERATE_SYSTEM_PROMPT,
    GENERATE_USER_PROMPT,
    REWRITE_SYSTEM_PROMPT,
    REWRITE_USER_PROMPT,
    HALLUCINATION_SYSTEM_PROMPT,
    HALLUCINATION_USER_PROMPT,
    SAFE_FALLBACK_RESPONSE,
)
from .memory import build_few_shot_section, log_correction, save_run_to_memory

# ── Mock document corpus ──────────────────────────────────────────────────────

MOCK_TAX_CHUNKS: list[dict[str, Any]] = [
    {
        "id": "chunk_001",
        "article": "Wet IB 2001, Art. 2.10",
        "text": (
            "Voor het belastbare inkomen uit werk en woning (box 1) gelden in 2024 de volgende tarieven: "
            "tot € 75.518 geldt een tarief van 36,97%; boven € 75.518 geldt een tarief van 49,50%. "
            "Het maximale heffingskorting voor arbeidsinkomen bedraagt € 5.532."
        ),
        "source": "Wet inkomstenbelasting 2001",
        "year": 2024,
    },
    {
        "id": "chunk_002",
        "article": "Wet IB 2001, Art. 4.6",
        "text": (
            "Aanmerkelijk belang (box 2) betreft een belang van 5% of meer in een vennootschap. "
            "Het tarief voor box 2 inkomen is in 2024: 24,5% over de eerste € 67.000 en 33% over het meerdere. "
            "Dividenden en vermogenswinsten uit aanmerkelijk belang vallen onder box 2."
        ),
        "source": "Wet inkomstenbelasting 2001",
        "year": 2024,
    },
    {
        "id": "chunk_003",
        "article": "Wet IB 2001, Art. 5.2",
        "text": (
            "Voor box 3 (sparen en beleggen) geldt een fictief rendement op vermogen. "
            "Het heffingvrij vermogen is in 2024 € 57.000 per persoon (€ 114.000 voor fiscale partners). "
            "Het belastingtarief voor box 3 bedraagt 36%."
        ),
        "source": "Wet inkomstenbelasting 2001",
        "year": 2024,
    },
    {
        "id": "chunk_004",
        "article": "Wet OB 1968, Art. 9",
        "text": (
            "Het algemene btw-tarief is 21% (Wet OB 1968, Art. 9 lid 1). "
            "Het verlaagde tarief van 9% geldt voor levensmiddelen, geneesmiddelen, boeken en bepaalde diensten. "
            "Het 0%-tarief geldt voor export en intracommunautaire leveringen."
        ),
        "source": "Wet op de omzetbelasting 1968",
        "year": 2024,
    },
    {
        "id": "chunk_005",
        "article": "Wet DB 1965, Art. 1",
        "text": (
            "Dividendbelasting wordt geheven van degene aan wie het dividend wordt uitbetaald. "
            "Het tarief bedraagt 15% (Wet DB 1965, Art. 1 lid 2). "
            "Dividendbelasting is verrekenbaar met de verschuldigde inkomstenbelasting of vennootschapsbelasting."
        ),
        "source": "Wet op de dividendbelasting 1965",
        "year": 2024,
    },
    {
        "id": "chunk_006",
        "article": "Wet VPB 1969, Art. 22",
        "text": (
            "Het tarief voor de vennootschapsbelasting (VPB) is in 2024 als volgt: "
            "19% over de eerste € 200.000 belastbare winst; "
            "25,8% over het belastbare bedrag boven € 200.000 (Wet VPB 1969, Art. 22). "
            "Dit gedifferentieerde tarief geldt voor alle vpb-plichtige lichamen."
        ),
        "source": "Wet op de vennootschapsbelasting 1969",
        "year": 2024,
    },
]

# Keywords that map to each chunk (for mock retrieval)
_CHUNK_KEYWORDS: list[tuple[int, list[str]]] = [
    (0, ["box 1", "box1", "inkomen", "inkomstenbelasting", "income tax", "loon",
         "werk", "woning", "36,97", "49,50", "heffingskorting"]),
    (1, ["box 2", "box2", "aanmerkelijk", "ab-houder", "aanmerkelijk belang"]),
    (2, ["box 3", "box3", "vermogen", "sparen", "beleggen", "fictief rendement",
         "heffingvrij"]),
    (3, ["btw", "omzetbelasting", "vat", "belasting toegevoegde waarde", "21%", "9%"]),
    (4, ["dividend", "dividendbelasting", "15%"]),
    (5, ["winst", "vennootschap", "vpb", "vennootschapsbelasting", "corporate tax",
         "winstbelasting", "profit tax"]),
]


# ── LLM backend ───────────────────────────────────────────────────────────────

def _backend() -> str:
    """Return the active LLM backend: 'anthropic', 'hermes', or 'mock'."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("HERMES_API_KEY") or os.getenv("HERMES_BASE_URL"):
        return "hermes"
    return "mock"


def _llm_call(model: str, system: str, user: str, max_tokens: int = 256) -> str:
    """Unified LLM call — routes to the active backend.

    Hermes note: Hermes ignores the `model` field and uses its configured model
    (claude-sonnet-4-6 by default).  To change this, set API_SERVER_MODEL_NAME
    in ~/.hermes/.env before starting the gateway.
    """
    backend = _backend()

    if backend == "anthropic":
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()

    if backend == "hermes":
        from openai import OpenAI  # noqa: PLC0415
        client = OpenAI(
            base_url=os.getenv("HERMES_BASE_URL", "http://localhost:8642/v1"),
            api_key=os.getenv("HERMES_API_KEY", "crag-poc-local"),
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()

    raise RuntimeError("No LLM backend available — this path should not be reached")


def _mock_retrieve(query: str) -> list[dict]:
    """Keyword-based retrieval over the mock corpus."""
    q = query.lower()
    results = [MOCK_TAX_CHUNKS[idx] for idx, kws in _CHUNK_KEYWORDS if any(kw in q for kw in kws)]
    # Out-of-domain or unrecognised: return one chunk the grader will mark IRRELEVANT
    return results or [MOCK_TAX_CHUNKS[0]]


def _chunks_to_text(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{c['article']}]\n{c['text']}" for c in chunks)


def _parse_score(raw: str) -> float:
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", raw)
    score = float(match.group()) if match else 0.5
    return max(0.0, min(1.0, score))


# ── Node: retrieve ────────────────────────────────────────────────────────────

@traceable(name="retrieve")
def retrieve_node(state: dict) -> dict:
    chunks = _mock_retrieve(state["query"])
    return {"chunks": chunks}


# ── Node: grade ───────────────────────────────────────────────────────────────

@traceable(name="grade")
def grade_node(state: dict) -> dict:
    query = state["query"]
    chunks: list[dict] = state.get("chunks", [])

    if _backend() == "mock":
        q = query.lower()
        specific_terms = [
            "box 1", "box 2", "box 3", "box1", "box2", "box3",
            "inkomstenbelasting", "vennootschapsbelasting", "omzetbelasting",
            "dividendbelasting", "income tax", "corporate tax",
            "aanmerkelijk belang", "btw", "vpb", "heffingvrij", "fictief rendement",
            "art.", "artikel", "2024", "2023", "tarief", "rate",
        ]
        grade = "RELEVANT" if any(t in q for t in specific_terms) else "IRRELEVANT"
        return {"grades": [grade] * len(chunks)}

    grades: list[str] = []
    for chunk in chunks:
        raw = _llm_call(
            model="claude-sonnet-4-6",
            system=GRADE_SYSTEM_PROMPT,
            user=GRADE_USER_PROMPT.format(
                query=query, chunk_text=chunk["text"], article=chunk["article"]
            ),
            max_tokens=16,
        ).upper()
        if "IRRELEVANT" in raw:
            grade = "IRRELEVANT"
        elif "PARTIAL" in raw:
            grade = "PARTIAL"
        else:
            grade = "RELEVANT"
        grades.append(grade)

    return {"grades": grades}


# ── Node: rewrite ─────────────────────────────────────────────────────────────

@traceable(name="rewrite")
def rewrite_node(state: dict) -> dict:
    query = state["query"]
    rewrite_count = state.get("rewrite_count", 0)

    if _backend() == "mock":
        rewrites = [
            f"{query} vennootschapsbelasting tarief 2024",
            f"Nederlandse belastingwetgeving {query} inkomstenbelasting box 1 2024",
        ]
        new_query = rewrites[min(rewrite_count, len(rewrites) - 1)]
        return {"query": new_query, "rewrite_count": rewrite_count + 1}

    new_query = _llm_call(
        model="claude-sonnet-4-6",
        system=REWRITE_SYSTEM_PROMPT,
        user=REWRITE_USER_PROMPT.format(query=query, rewrite_count=rewrite_count + 1),
        max_tokens=128,
    )
    return {"query": new_query, "rewrite_count": rewrite_count + 1}


# ── Node: generate ────────────────────────────────────────────────────────────

@traceable(name="generate")
def generate_node(state: dict) -> dict:
    query = state["query"]
    chunks: list[dict] = state.get("chunks", [])
    grades: list[str] = state.get("grades", [])

    # Use only relevant/partial chunks if grades are available
    if grades:
        filtered = [c for c, g in zip(chunks, grades) if g != "IRRELEVANT"]
        chunks_for_prompt = filtered if filtered else chunks
    else:
        chunks_for_prompt = chunks

    chunk_text = _chunks_to_text(chunks_for_prompt)
    few_shot = build_few_shot_section()

    if _backend() == "mock":
        if not chunks_for_prompt:
            return {"answer": SAFE_FALLBACK_RESPONSE}
        first = chunks_for_prompt[0]
        return {
            "answer": (
                f"[MOCK ANSWER — set ANTHROPIC_API_KEY or HERMES_API_KEY for real generation]\n\n"
                f"Based on {first['article']}: {first['text'][:200]}…"
            )
        }

    answer = _llm_call(
        model="claude-opus-4-7",
        system=GENERATE_SYSTEM_PROMPT,
        user=GENERATE_USER_PROMPT.format(
            chunks=chunk_text, few_shot_section=few_shot, query=query
        ),
        max_tokens=1024,
    )
    return {"answer": answer}


# ── Node: hallucination_check ─────────────────────────────────────────────────

@traceable(name="hallucination_check")
def hallucination_check_node(state: dict) -> dict:
    query = state["query"]
    original_query = state.get("original_query", query)
    answer = state.get("answer", "")
    chunks: list[dict] = state.get("chunks", [])
    grades: list[str] = state.get("grades", [])

    chunk_text = _chunks_to_text(chunks)

    if _backend() == "mock":
        tax_words = ["belasting", "tax", "box", "btw", "inkomen", "winst",
                     "dividend", "vpb", "vennootschap", "heffing", "aftrek"]
        score = 0.9 if any(w in original_query.lower() for w in tax_words) else 0.2
        is_flagged = score < 0.7
        _persist(original_query, answer, grades, chunks, score, is_flagged)
        return {
            "answer": SAFE_FALLBACK_RESPONSE if is_flagged else answer,
            "hallucination_score": score,
            "is_flagged": is_flagged,
        }

    # Domain-violation sentinel from the generator — skip LLM call
    if answer.startswith("DOMAIN_VIOLATION"):
        score = 0.0
        _persist(original_query, answer, grades, chunks, score, is_flagged=True)
        return {"answer": SAFE_FALLBACK_RESPONSE, "hallucination_score": 0.0, "is_flagged": True}

    raw_score = _llm_call(
        model="claude-sonnet-4-6",
        system=HALLUCINATION_SYSTEM_PROMPT,
        user=HALLUCINATION_USER_PROMPT.format(
            chunks=chunk_text, query=original_query, answer=answer
        ),
        max_tokens=16,
    )
    score = _parse_score(raw_score)
    is_flagged = score < 0.7

    _persist(original_query, answer, grades, chunks, score, is_flagged)

    return {
        "answer": SAFE_FALLBACK_RESPONSE if is_flagged else answer,
        "hallucination_score": score,
        "is_flagged": is_flagged,
    }


def _persist(
    query: str,
    answer: str,
    grades: list[str],
    chunks: list[dict],
    score: float,
    is_flagged: bool,
) -> None:
    grade_summary = {"grades": grades, "chunks_used": len(chunks)}
    if is_flagged:
        log_correction(query, answer, score)
    save_run_to_memory(
        query,
        SAFE_FALLBACK_RESPONSE if is_flagged else answer,
        grade_summary,
        is_flagged=is_flagged,
    )

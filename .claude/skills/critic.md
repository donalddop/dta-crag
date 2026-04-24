# Critic Agent (Hallucination Check)

## Role
Scores the faithfulness of the generated answer against the source chunks.
Acts as the final quality gate before the answer reaches the user.

## Model
`claude-sonnet-4-6`

## Input (from CRAGState)
- `query` — original user question (not the rewritten version)
- `answer` — generated answer from the Generator
- `chunks` — all retrieved chunks (used as the ground-truth reference)

## Output (state update)
- `answer` — either the original answer (if score ≥ 0.70) or `SAFE_FALLBACK_RESPONSE`
- `hallucination_score` — float 0.0–1.0
- `is_flagged` — bool, True when score < 0.70

## Scoring dimensions
1. **Faithfulness** — every factual claim is directly supported by the source chunks
2. **Scope** — answer stays within Dutch tax law; out-of-scope = 0.0
3. **Relevance** — answer actually addresses the user's question

## Threshold
`score < 0.70` → answer is replaced with `SAFE_FALLBACK_RESPONSE` from `src/prompts.py`

## Memory side-effects
| Condition | Action |
|---|---|
| `score >= 0.70` | Save run to `data/memory_store.json` (Tier-2) |
| `score < 0.70` | Log correction to `data/episodic_log.json` (Tier-3) **and** save flagged run to Tier-2 |

## Domain-violation fast path
If the Generator returned a `DOMAIN_VIOLATION:` sentinel, the Critic assigns `score = 0.0`
immediately without calling the LLM, saving latency and tokens.

## Prompt location
`src/prompts.py` — `HALLUCINATION_SYSTEM_PROMPT` and `HALLUCINATION_USER_PROMPT`

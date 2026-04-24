# Generator Agent

## Role
Synthesises a grounded answer from the retrieved (and graded) source chunks.
Uses only relevant/partial chunks; refuses out-of-domain questions.

## Model
`claude-opus-4-7`

## Input (from CRAGState)
- `query` — current (possibly rewritten) query
- `chunks` — retrieved chunks
- `grades` — chunk classifications
- Tier-2 memory: top-3 recent successful Q&A pairs injected as few-shot examples

## Output (state update)
- `answer` — synthesised answer string

## Domain enforcement
If the question is outside Dutch tax law scope, the generator outputs:
```
DOMAIN_VIOLATION: This question falls outside Dutch tax law scope.
```
The Critic node detects this sentinel and immediately assigns `score = 0.0`,
triggering the safe fallback without wasting a hallucination-check call.

## Prompt location
`src/prompts.py` — `GENERATE_SYSTEM_PROMPT` and `GENERATE_USER_PROMPT`

## Few-shot examples
Injected from Tier-2 memory (`data/memory_store.json`) via `memory.build_few_shot_section()`.
Only non-flagged runs are used as examples.

## Citation requirement
Every factual claim must reference an article number, e.g.:
> "Onder Wet IB 2001, Art. 2.10 geldt een tarief van 36,97% tot € 75.518."

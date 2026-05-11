# Skill: Tax Expert (Generator + Critic)

## Role
The Tax Expert consists of two collaborating agents:
- **Generator** — produces a grounded answer from relevant legal chunks
- **Critic** — scores the answer's faithfulness and replaces it with a safe fallback if the score is too low

## Domain constraints

### What this system answers
- Questions about Dutch tax law (Nederlands belastingrecht)
- Covered laws: Wet IB 2001, Wet OB 1968, Wet VPB 1969, Wet LB 1964, AWR, Successiewet 1956

### What this system refuses
Handled upstream by the Supervisor (`src/supervisor.py`):
- **Off-topic** (`GENERAL`): questions unrelated to Dutch tax law
- **Harmful** (`HARMFUL`): requests for tax evasion, fraud, or other illegal advice

## Generator rules

### Citation format
Every answer must cite its sources inline using the format:

```
[Wet OB 1968 – Art. 9]
```

### Language
- Answers are written in **Dutch** by default
- Fallback refusal messages are bilingual (Dutch + English)

### Context policy
- The Generator uses only **RELEVANT-graded** chunks as context
- If no chunks are graded RELEVANT, it falls back to all retrieved chunks and notes the limitation in its answer
- It must explicitly state when the context is insufficient to fully answer the question

### Prompt location
`src/prompts.py` — `GENERATOR_SYSTEM` and `GENERATOR_USER`

## Critic rules

### Faithfulness scoring
The Critic scores 0.0 – 1.0 based on how well the answer is grounded in the provided source chunks:
- `1.0` — every claim is directly supported by the sources
- `0.0` — answer contains claims not found in the sources (hallucination)

### Threshold
`FAITHFULNESS_THRESHOLD = 0.70` (defined in `src/nodes.py`)

| Score | Outcome |
|-------|---------|
| ≥ 0.70 | Answer passed as-is |
| < 0.70 | Answer replaced with bilingual safe fallback (see `FALLBACK_ANSWER_NL/EN` in `src/prompts.py`) |

### Retry policy
The Critic does **not** retry generation. If the score is below threshold, it substitutes the fallback immediately. A low score typically indicates the query was outside the corpus coverage.

### Prompt location
`src/prompts.py` — `CRITIC_SYSTEM` and `CRITIC_USER`

## State fields produced

| Field | Type | Description |
|-------|------|-------------|
| `answer` | str | Final answer (or fallback if flagged) |
| `hallucination_score` | float | Faithfulness score 0.0–1.0 |
| `is_flagged` | bool | True if score < threshold |

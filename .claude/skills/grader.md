# Grader Agent

## Role
Classifies each retrieved chunk as RELEVANT, PARTIAL, or IRRELEVANT with respect to
the current query. Controls whether the graph rewrites the query or proceeds to generation.

## Model
`claude-sonnet-4-6`

## Input (from CRAGState)
- `query` — current search query
- `chunks` — list of retrieved chunks

## Output (state update)
- `grades` — list of strings, one per chunk: `"RELEVANT"`, `"PARTIAL"`, or `"IRRELEVANT"`

## Grading rubric
| Grade | When to use |
|---|---|
| RELEVANT | Chunk directly addresses the question with specific, usable information |
| PARTIAL | Chunk has related information but doesn't fully cover the question |
| IRRELEVANT | Chunk does not address the question at all |

## Branch trigger (in `src/graph.py`)
```
if majority(grades == IRRELEVANT) and rewrite_count < 2:
    → rewrite
else:
    → generate
```

## Prompt location
`src/prompts.py` — `GRADE_SYSTEM_PROMPT` and `GRADE_USER_PROMPT`

## Mock fallback
When `ANTHROPIC_API_KEY` is not set: grades RELEVANT for tax-keyword queries, IRRELEVANT otherwise.

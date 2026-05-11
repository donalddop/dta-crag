"""
Pre-interview warm-up script.

Run this once before your demo to:
  1. Download the sentence-transformers model (~120 MB, cached after first run)
  2. Build and persist the Chroma vector index
  3. Fire a single test query end-to-end (confirms your API key works)

Usage:
    python warmup.py

Expected output: a short answer about VPB rates, plus a ✓ on each step.
After this, `streamlit run app.py` will start instantly with no download delay.
"""

from __future__ import annotations

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

def check(label: str, fn):
    print(f"  {label}...", end=" ", flush=True)
    t0 = time.time()
    result = fn()
    print(f"✓  ({time.time() - t0:.1f}s)")
    return result

print("\n⚙  dta-crag warm-up\n")

# 1. API key
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if not api_key or api_key.startswith("sk-ant-test"):
    sys.exit(
        "✗  ANTHROPIC_API_KEY not set.\n"
        "   Copy .env.example to .env and paste your real key, then re-run."
    )
print(f"  API key       ✓  ({api_key[:12]}…)")

# 2. Embedding model + Chroma index
check(
    "Embedding model + vector index",
    lambda: __import__("src.retriever", fromlist=["retrieve"]).retrieve("test", k=1),
)

# 3. Full pipeline
print("  Full pipeline...", end=" ", flush=True)
t0 = time.time()
from src.graph import run_pipeline
state = run_pipeline("Wat is het tarief voor vennootschapsbelasting in 2024?")
elapsed = time.time() - t0
print(f"✓  ({elapsed:.1f}s)")

# 4. Report
print(f"\n{'─' * 60}")
print(f"Q: {state['original_query']}")
print(f"\nA: {state['answer'][:400]}")
print(f"\n  Faithfulness : {state['hallucination_score']:.0%}")
print(f"  Flagged      : {state['is_flagged']}")
print(f"  Rewrites     : {state['rewrite_count']}")
print(f"{'─' * 60}")
print("\n✅  All good. Run `streamlit run app.py` when ready.\n")

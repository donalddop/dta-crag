"""
Supervisor agent — classifies incoming queries and routes them.

  TAX      → CRAG pipeline (retrieve → grade → generate → critique)
  GENERAL  → polite off-topic refusal (no pipeline call)
  HARMFUL  → firm refusal for fraud / evasion requests

This is the single public entry point used by main.py and demo.py.
"""

from __future__ import annotations

from .nodes import _call
from .logging_config import get_agent_logger

_log = get_agent_logger("SUPERVISOR")

# ── Prompts ───────────────────────────────────────────────────────────────────

_CLASSIFIER_SYSTEM = """\
Je bent een supervisor die bepaalt of een vraag geschikt is voor een Nederlands belastingadviessysteem.

Classificeer de vraag als exact één van:
- TAX     : een legitieme vraag over Nederlands belastingrecht
- GENERAL : een vraag buiten het domein van Nederlands belastingrecht
- HARMFUL : een verzoek om hulp bij belastingfraude, belastingontduiking of andere illegale activiteiten

Antwoord uitsluitend met één woord: TAX, GENERAL of HARMFUL."""

_CLASSIFIER_USER = "Vraag: {query}\n\nClassificatie:"

_REFUSAL_GENERAL = """\
Deze vraag valt buiten het domein van dit systeem.

Ik ben gespecialiseerd in Nederlands belastingrecht en kan alleen \
belastingvragen beantwoorden. Stel een belastingvraag of raadpleeg \
een andere bron voor algemene vragen.

---

This question is outside the scope of this system.
I specialise in Dutch tax law. Please ask a tax-related question \
or consult another source for general queries."""

_REFUSAL_HARMFUL = """\
⛔ Dit verzoek kan ik niet beantwoorden.

U vraagt om assistentie bij belastingontduiking of -fraude. Dit is \
strafbaar op grond van art. 68/69 Algemene wet inzake rijksbelastingen \
(AWR) en kan leiden tot boetes tot 300 % van de verschuldigde belasting \
en/of gevangenisstraf.

Voor legitieme belastingoptimalisatie kunt u een gecertificeerd \
belastingadviseur raadplegen.

---

⛔ This request cannot be fulfilled.

Assisting with tax evasion or fraud is a criminal offence under Dutch \
law (AWR art. 68/69). Please consult a certified tax advisor for \
legitimate tax planning."""


# ── Public API ────────────────────────────────────────────────────────────────

def route(query: str) -> dict:
    """
    Classify the query and run the appropriate agent.

    Returns a dict:
        domain   : "tax" | "general" | "harmful"
        answer   : str
        refusal  : bool
        state    : CRAGState | None   (only for domain=="tax")
    """
    short = query[:80] + ("…" if len(query) > 80 else "")
    _log.info(f'Received query: "{short}"')
    _log.info("Classifying query domain…")

    raw = _call(_CLASSIFIER_SYSTEM, _CLASSIFIER_USER.format(query=query), max_tokens=10)
    classification = raw.strip().upper()

    if "HARMFUL" in classification:
        domain = "HARMFUL"
    elif "GENERAL" in classification:
        domain = "GENERAL"
    else:
        domain = "TAX"

    _log.info(f"Classification: {domain}")

    if domain == "TAX":
        _log.info("→ Routing to TAX_AGENT (CRAG pipeline)")
        from .graph import run_pipeline
        state = run_pipeline(query)
        return {"domain": "tax", "answer": state["answer"], "refusal": False, "state": state}

    if domain == "HARMFUL":
        _log.info("→ REFUSING: harmful / illegal request")
        return {"domain": "harmful", "answer": _REFUSAL_HARMFUL, "refusal": True, "state": None}

    # GENERAL
    _log.info("→ REFUSING: off-topic (not Dutch tax law)")
    return {"domain": "general", "answer": _REFUSAL_GENERAL, "refusal": True, "state": None}

"""
Console logging for dta-crag agents.

Call setup_logging() once at startup (main.py / demo.py).
Each node then logs via get_agent_logger("GRADER") etc.
"""

from __future__ import annotations

import logging
import sys

# ANSI colors per agent role
_COLORS = {
    "SUPERVISOR": "\033[35m",   # Magenta
    "RETRIEVER":  "\033[36m",   # Cyan
    "GRADER":     "\033[33m",   # Yellow
    "REWRITER":   "\033[34m",   # Blue
    "GENERATOR":  "\033[32m",   # Green
    "CRITIC":     "\033[31m",   # Red
    "MEMORY":     "\033[90m",   # Dark grey
}
_RESET = "\033[0m"
_DIM   = "\033[2m"


class _AgentFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        agent = getattr(record, "agent", "SYSTEM")
        color = _COLORS.get(agent, "")
        tag   = f"{color}[{agent:<10}]{_RESET}"
        return f"{tag} {record.getMessage()}"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the dta_crag logger.  Call once before the first pipeline run."""
    root = logging.getLogger("dta_crag")
    if root.handlers:
        return  # already configured
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_AgentFormatter())
    root.addHandler(handler)
    root.propagate = False


def get_agent_logger(agent: str) -> logging.LoggerAdapter:
    """Return a LoggerAdapter that tags every record with agent=<agent>."""
    logger = logging.getLogger(f"dta_crag.{agent.lower()}")
    return logging.LoggerAdapter(logger, {"agent": agent})

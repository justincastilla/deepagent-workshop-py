"""
Elastic subagent — SOLUTION.

Drop-in replacement for src/subagents/elastic.py.
Reference only — gitignored, never ship to attendees.
"""

from __future__ import annotations

from pathlib import Path

from src.tools.ask_elastic_agent import ask_elastic_agent

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "elastic.md"
elastic_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

elastic_subagent: dict = {
    "name": "elastic-agent",
    "description": (
        "Use to retrieve cached or historical research data from Elasticsearch: "
        "prior research reports, technology snapshots, time-series trends, "
        "adoption signals, and similar technologies via semantic search. "
        "Always check elastic-agent BEFORE triggering fresh data collection "
        "from other subagents — the data may already exist."
    ),
    "system_prompt": elastic_prompt,
    "tools": [ask_elastic_agent],
}

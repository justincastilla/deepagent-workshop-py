"""
Orchestrator — the top-level deep agent.

Dispatches user queries to one of four specialist subagents:
  - metrics-agent   (GitHub stats)
  - sentiment-agent (community mood)
  - web-agent       (adoption signals)
  - elastic-agent   (cached/historical research data)

Each subagent has its own system prompt and tools. The orchestrator
itself reads its prompt from src/prompts/orchestrator.md. The elastic
subagent ships stubbed — that's the workshop hands-on segment.
"""

from __future__ import annotations

from pathlib import Path

from deepagents import create_deep_agent

from src.llm import create_llm
from src.subagents.elastic import elastic_subagent
from src.subagents.metrics import metrics_subagent
from src.subagents.sentiment import sentiment_subagent
from src.subagents.web import web_subagent

_PROMPT_PATH = Path(__file__).parent / "prompts" / "orchestrator.md"
orchestrator_prompt = _PROMPT_PATH.read_text(encoding="utf-8")

orchestrator = create_deep_agent(
    model=create_llm(),
    system_prompt=orchestrator_prompt,
    subagents=[
        metrics_subagent,
        sentiment_subagent,
        web_subagent,
        elastic_subagent,
    ],
)

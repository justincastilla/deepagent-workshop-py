"""
LLM factory — single source of truth for how the workshop talks to a model.

Every subagent and the orchestrator construct their model via create_llm().
The model client is a standard LangChain ChatOpenAI pointed at the workshop's
LiteLLM proxy via base_url. The proxy speaks the OpenAI HTTP API but routes
UPSTREAM to a Claude Sonnet deployment hosted on Azure AI Foundry.

Why this matters: Attendees never need their own API key. They paste a
workshop-issued LITELLM_API_KEY + LITELLM_API_BASE into .env and everything
downstream Just Works.
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value or not value.strip():
        raise RuntimeError(
            f"Missing required env var {name}. "
            "Copy .env.example to .env and fill in the values from your instructor."
        )
    return value


def create_llm(
    *,
    model: Optional[str] = None,
    temperature: float = 0.5,
    max_tokens: Optional[int] = None,
) -> ChatOpenAI:
    """Build a ChatOpenAI client pointed at the workshop LiteLLM proxy.

    Examples:
        Default model (Sonnet via the workshop proxy):
            llm = create_llm()

        Override model alias:
            llm = create_llm(model="llm-gateway/some-other-alias")
    """
    api_key = _require_env("LITELLM_API_KEY")
    base_url = _require_env("LITELLM_API_BASE")
    resolved_model = (
        model or os.environ.get("LLM_MODEL") or "llm-gateway/claude-sonnet-4-5"
    )

    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=resolved_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

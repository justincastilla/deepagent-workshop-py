"""
Kibana Agent Builder client — PRE-PROVIDED.

In the JS version of this workshop, building this client is Build Step 1.
For the 50-minute Python version we hand it to you ready-made so the
hands-on time can focus on the agent code in subagents/elastic.py and
tools/ask_elastic_agent.py.

Talks to /api/agent_builder/converse on a Kibana cluster running the
Agent Builder feature. The endpoint accepts natural-language input and
returns the agent's reply along with a conversation_id that can be
passed back in follow-up calls to maintain multi-turn context.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class ConverseRequest:
    agent_id: str
    """The Kibana Agent Builder agent UUID (from .env: ELASTIC_AGENT_ID)."""

    input: str
    """Natural-language input for the agent."""

    conversation_id: Optional[str] = None
    """Optional. Pass to continue an existing multi-turn conversation."""


@dataclass
class ConverseResponse:
    text: str
    """The agent's text reply."""

    conversation_id: str
    """Conversation handle for follow-up turns."""


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(
            f"Missing env var {name}. "
            "Did you copy .env.example to .env and fill it in?"
        )
    return v


def converse(req: ConverseRequest) -> ConverseResponse:
    """Send a natural-language prompt to the workshop's Kibana Agent Builder
    instance and return the agent's reply.

    Example:
        resp = converse(ConverseRequest(
            agent_id=os.environ["ELASTIC_AGENT_ID"],
            input="Find technologies similar to 'real-time observability'",
        ))
        print(resp.text)
    """
    kibana_url = _require_env("KIBANA_URL").rstrip("/")
    api_key = _require_env("ELASTICSEARCH_API_KEY")

    url = f"{kibana_url}/api/agent_builder/converse"
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
    }
    body: dict = {
        "agent_id": req.agent_id,
        "input": req.input,
    }
    if req.conversation_id:
        body["conversation_id"] = req.conversation_id

    res = httpx.post(url, headers=headers, json=body, timeout=120.0)
    if res.is_error:
        raise RuntimeError(
            f"Kibana Agent Builder returned {res.status_code} {res.reason_phrase}: "
            f"{res.text[:600]}"
        )

    data = res.json()
    response_field = data.get("response")
    if isinstance(response_field, str):
        text = response_field
    elif isinstance(response_field, dict):
        text = response_field.get("message", "") or ""
    else:
        text = ""

    return ConverseResponse(
        text=text,
        conversation_id=data.get("conversation_id", "") or "",
    )

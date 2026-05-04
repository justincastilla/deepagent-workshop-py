"""
ask_elastic_agent tool — Build B complete.

The LangChain tool the elastic subagent uses to delegate data retrieval
to Kibana Agent Builder. Wraps the pre-provided kibana_client.converse()
in a @tool decorator with a docstring the orchestrator's LLM reads to
decide when to use it.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool

from src.tools.kibana_client import ConverseRequest, converse


@tool
def ask_elastic_agent(query: str, conversation_id: str = "") -> str:
    """Send a natural-language request to the Elastic Agent and return its
    response.

    The agent has access to ES|QL tools for searching, retrieving, and
    analysing technology research data stored in Elasticsearch. Use this
    for any data retrieval from Elasticsearch, including:

      - Finding similar technologies via semantic search
      - Retrieving historical snapshots and trend data
      - Getting adoption signals
      - Fetching past research reports

    Be specific in queries: include full repo names (e.g.
    'elastic/elasticsearch') and time ranges where relevant.

    Args:
        query: Natural-language description of what data to fetch.
            Examples: "Find technologies similar to real-time observability",
            "Get the latest research report for elastic/elasticsearch".
        conversation_id: Optional. Pass to continue a multi-turn
            conversation with the Elastic Agent.
    """
    agent_id = os.environ.get("ELASTIC_AGENT_ID")
    if not agent_id:
        raise RuntimeError("Missing ELASTIC_AGENT_ID in .env")

    resp = converse(
        ConverseRequest(
            agent_id=agent_id,
            input=query,
            conversation_id=conversation_id or None,
        )
    )
    return resp.text

"""
ask_elastic_agent tool — TODO (Build B).

The LangChain tool the elastic subagent uses to delegate data retrieval
to Kibana Agent Builder.

Build B is the second hands-on segment. Wrap the pre-provided Kibana
client (src/tools/kibana_client.py) as a tool the subagent can call.

When you're done, run:

    python scripts/test_tool.py

If that prints a reply from the agent, you're cleared to move on.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool

from src.tools.kibana_client import ConverseRequest, converse


# ---------------------------------------------------------------------
# TODO: implement this tool.
#
# Things to fill in:
#   1. The function signature: a `query` string (required) and an
#      optional `conversation_id` string.
#   2. The docstring: tell the LLM exactly when to use this tool — what
#      the agent on the other side is good at (semantic search for
#      similar technologies, retrieving cached research reports,
#      historical snapshots, trend data, adoption signals). Encourage
#      specific queries with full repo names + time ranges.
#   3. The body: read ELASTIC_AGENT_ID from os.environ, call converse()
#      with a ConverseRequest, return the .text field.
# ---------------------------------------------------------------------
@tool
def ask_elastic_agent(query: str, conversation_id: str = "") -> str:
    """TODO: describe when the orchestrator should call ask_elastic_agent."""
    raise NotImplementedError(
        "ask_elastic_agent is not implemented yet — finish Build B."
    )

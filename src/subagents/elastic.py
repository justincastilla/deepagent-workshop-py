"""
Elastic subagent — TODO (Build A).

This is the workshop's centerpiece. Build A is the FIRST hands-on
segment: wire the system prompt, the tool list, and a description into
a deepagents subagent definition.

The orchestrator (src/orchestrator.py) already imports `elastic_subagent`
from this file, so once you finish here AND finish Build B
(src/tools/ask_elastic_agent.py), the orchestrator will dispatch to
this subagent for any cached/historical research data lookup.

Reference any of the working subagents (metrics.py, sentiment.py,
web.py) for the exact shape.
"""

from __future__ import annotations

from pathlib import Path

from src.tools.ask_elastic_agent import ask_elastic_agent

# ---------------------------------------------------------------------
# TODO 1: load the system prompt from src/prompts/elastic.md.
#
# Look at how metrics.py / sentiment.py / web.py do this. The pattern
# is the same: build a Path off __file__, read the file, store the
# string in a module-level variable.
#
# Replace this placeholder with the real prompt-load.
# ---------------------------------------------------------------------
elastic_prompt = "TODO: load src/prompts/elastic.md and replace this string."


# ---------------------------------------------------------------------
# TODO 2: replace the placeholder description below with one that tells
# the orchestrator WHEN to dispatch to elastic-agent.
#
# A deepagents subagent is a plain dict with these keys:
#
#   {
#     "name":          str,            # short slug — "elastic-agent"
#     "description":   str,            # tells the orchestrator WHEN to dispatch
#                                      # to this subagent. Be specific.
#     "system_prompt": str,            # the system prompt you loaded above
#     "tools":         list[Tool],     # tools this subagent may call
#   }
#
# For the description: emphasise that the orchestrator should ALWAYS
# check elastic-agent FIRST for cached/historical data before kicking
# off fresh data collection from metrics/sentiment/web.
#
# The values below are placeholders — they let the server start without
# crashing, but the elastic subagent will be useless until you fix them.
# ---------------------------------------------------------------------
elastic_subagent: dict = {
    "name": "elastic-agent",
    "description": "TODO: describe when the orchestrator should dispatch to elastic-agent.",
    "system_prompt": elastic_prompt,
    "tools": [ask_elastic_agent],
}

<!--
  Elastic subagent system prompt — TODO (Build A · part of TODO 2).

  This file is loaded by src/subagents/elastic.py and injected as the
  system message for every elastic-agent invocation. The deepagents
  library handles the wiring; you just provide the content.

  Aim for ~30-60 lines. Use markdown — both the LLM and any human
  reading the activity panel will appreciate the structure.

  Cover these five sections:

    1. Identity — who is this agent? (e.g. "You are an Elastic Data
       Specialist.") One sentence.

    2. Mission — what is the agent responsible for? Retrieving research
       data from Elasticsearch via the ask_elastic_agent tool. The
       Elastic Agent on the other side handles ES|QL construction —
       this subagent just asks clearly and reports the results.

    3. Tool guidance — how to use ask_elastic_agent well:
       - include full repo names (elastic/elasticsearch, not elasticsearch)
       - include time ranges where relevant
       - 3-4 concrete example queries (cached report, similar tech via
         semantic search, adoption signals, trend data)
       - mention conversation_id for multi-turn follow-ups

    4. Output format — a markdown skeleton the agent should fill in
       (## Elasticsearch Research Summary, ### Data Retrieved,
       ### Key Findings, ### Gaps).

    5. Honesty rule — never fabricate results. If the agent returns no
       data, report that clearly so the orchestrator can dispatch fresh
       research to other subagents.

  Delete this comment block once you've written the prompt.
-->

TODO: write the elastic-agent system prompt.

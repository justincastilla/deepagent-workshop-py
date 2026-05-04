# DevRel-DeepAgent — 50-minute Python workshop

A pared-down Python port of the [JS DevRel-DeepAgent workshop](https://github.com/justincastilla/deepagent_workshop).
Runs in 50 minutes. One hands-on segment: complete the elastic subagent and
its `askElasticAgent` tool, then watch the orchestrator dispatch to it
alongside three already-working specialist subagents.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in values
./es-sandbox/pre-setup.sh     # one-time — runs at home before workshop
```

On workshop day, after your instructor hands you a LiteLLM key:

```bash
./es-sandbox/workshop-day-setup.sh
python scripts/verify.py
```

If verify passes, you're ready.

## What you'll build

The repo ships with three working subagents (metrics, sentiment, web)
and one stubbed-out subagent (elastic). In the workshop you'll:

1. **Build A** — wire `subagents/elastic.py` (load prompt, set description, list tools).
2. **Build B** — implement `tools/ask_elastic_agent.py` (call the pre-provided `kibana_client`, return text).

When both stubs are filled in, the orchestrator dispatches to all four
subagents in parallel and the UI lights up four colored panels.

## License

MIT — see [LICENSE](LICENSE).

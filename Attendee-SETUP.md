# Workshop setup

A 50-minute workshop on building deep agents with Elastic Agent Builder.
You'll come in with a working environment and finish a stubbed-out
elastic subagent live.

## Before workshop day (10–15 minutes at home)

### 1. Prereqs

- Python 3.11+ (`python3 --version`)
- Docker Desktop running (for `start-local`)
- A GitHub Personal Access Token — no scopes needed for public repos. Create at <https://github.com/settings/tokens>.
- A free Tavily API key. Sign up at <https://app.tavily.com/>.

### 2. Clone and install

```
git clone https://github.com/justincastilla/deepagent_workshop_py
cd deepagent_workshop_py
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Stand up local Elasticsearch + Kibana

From the project root:

```
curl -fsSL https://elastic.co/start-local | sh
```

This drops an `elastic-start-local/` folder and brings up ES + Kibana
in Docker. Leave it running.

### 4. Run the pre-setup script

```
./es-sandbox/pre-setup.sh
```

It indexes seed data, registers the Kibana Agent Builder agent, and
prints the env-var values you need to paste into `.env`.

### 5. Fill in `.env`

Open `.env` and paste in the values from the pre-setup output, plus
your GitHub and Tavily keys. **Leave the `LITELLM_*` values for now** —
your instructor hands those out on workshop day.

### 6. Verify

```
python scripts/verify.py
```

You should see ~12 of 14 checks green. The two LiteLLM-related checks
fail until workshop day — that's expected.

## Workshop day

Your instructor will hand you a `LITELLM_API_KEY`. Drop it into `.env`,
then:

```
./es-sandbox/workshop-day-setup.sh
python scripts/verify.py
```

All 14 checks should be green. Open the workshop UI:

```
python -m server.app
```

Visit <http://localhost:3000>. The workshop hands-on starts here.

## What you'll build during the workshop

Two short stubs, in this order:

- **Build A** — `src/subagents/elastic.py`: load the prompt, set the
  description, list `ask_elastic_agent` as a tool. ~3 minutes.
- **Build B** — `src/tools/ask_elastic_agent.py`: implement the tool
  body — call the pre-provided `kibana_client.converse()` and return
  the text. ~5 minutes.

After Build B you can sanity-check with:

```
python scripts/test_tool.py
```

When both builds are done, restart the server and run a query in the
UI. You should see all four subagent panels light up — your
elastic-agent included.

## Troubleshooting

**`python scripts/verify.py` shows `Agent Builder agent responds: ✗`** —
You haven't run `workshop-day-setup.sh` yet, or the Kibana LLM
connector creation failed. Check `KIBANA_URL` is set and the connector
exists at *Stack Management → Connectors* in Kibana.

**`docker ps` shows nothing** — start-local containers stopped. Restart
with `cd elastic-start-local && docker compose up -d`.

**`ImportError` on first import** — re-activate your venv with
`source .venv/bin/activate`.

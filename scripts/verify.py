"""
Pre-workshop setup verification.

Run this AFTER `.env` is filled in to confirm everything's wired up
before workshop day. It checks env vars, then pings each service
(LiteLLM, Elasticsearch, Kibana, the Agent Builder agent, GitHub,
Tavily) and prints a green check or red X for each.

    python scripts/verify.py

If all checks pass, you're ready. If any fail, the hint after the X
tells you what to fix.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CheckResult:
    ok: bool
    message: str
    hint: Optional[str] = None


@dataclass
class Check:
    name: str
    run: Callable[[], CheckResult]


# ---------- ANSI helpers (no deps) -------------------------------------

GREEN = "\x1b[32m"
RED = "\x1b[31m"
DIM = "\x1b[2m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"


def green(s: str) -> str:
    return f"{GREEN}{s}{RESET}"


def red(s: str) -> str:
    return f"{RED}{s}{RESET}"


def dim(s: str) -> str:
    return f"{DIM}{s}{RESET}"


def bold(s: str) -> str:
    return f"{BOLD}{s}{RESET}"


# ---------- check helpers ----------------------------------------------


def check_env(name: str) -> CheckResult:
    v = os.environ.get(name)
    if not v or not v.strip():
        return CheckResult(
            ok=False,
            message="missing or empty",
            hint=f"Set {name} in your .env (see .env.example)",
        )
    return CheckResult(ok=True, message="set")


def ping_litellm() -> CheckResult:
    base = os.environ.get("LITELLM_API_BASE")
    key = os.environ.get("LITELLM_API_KEY")
    if not base or not key:
        return CheckResult(ok=False, message="env vars not set")
    try:
        res = httpx.get(
            f"{base.rstrip('/')}/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=8.0,
        )
        if res.is_error:
            return CheckResult(
                ok=False,
                message=f"HTTP {res.status_code}",
                hint=(
                    "Check LITELLM_API_KEY (the sk- value from your handout) "
                    "and LITELLM_API_BASE"
                ),
            )
        return CheckResult(ok=True, message="200 OK")
    except Exception as err:  # noqa: BLE001
        return CheckResult(
            ok=False,
            message=str(err),
            hint="Is the LITELLM_API_BASE URL correct? Are you online?",
        )


def ping_es() -> CheckResult:
    host = os.environ.get("ELASTICSEARCH_HOST")
    key = os.environ.get("ELASTICSEARCH_API_KEY")
    if not host or not key:
        return CheckResult(ok=False, message="env vars not set")
    try:
        res = httpx.get(
            f"{host.rstrip('/')}/_cluster/health?timeout=2s",
            headers={"Authorization": f"ApiKey {key}"},
            timeout=8.0,
        )
        if res.is_error:
            return CheckResult(
                ok=False,
                message=f"HTTP {res.status_code}",
                hint=(
                    "Is start-local running? Try `docker ps | grep es-local`. "
                    "If ES is up, check ELASTICSEARCH_API_KEY matches the value "
                    "in elastic-start-local/.env"
                ),
            )
        body = res.json()
        return CheckResult(
            ok=True,
            message=f"cluster={body.get('status')}, nodes={body.get('number_of_nodes')}",
        )
    except Exception as err:  # noqa: BLE001
        return CheckResult(
            ok=False,
            message=str(err),
            hint=(
                "Is ES reachable at ELASTICSEARCH_HOST? "
                "Default for start-local is http://localhost:9200"
            ),
        )


def ping_kibana() -> CheckResult:
    url = os.environ.get("KIBANA_URL")
    key = os.environ.get("ELASTICSEARCH_API_KEY")
    if not url or not key:
        return CheckResult(ok=False, message="env vars not set")
    try:
        res = httpx.get(
            f"{url.rstrip('/')}/api/status",
            headers={
                "Authorization": f"ApiKey {key}",
                "kbn-xsrf": "true",
            },
            timeout=8.0,
        )
        if res.is_error:
            return CheckResult(
                ok=False,
                message=f"HTTP {res.status_code}",
                hint=(
                    "Is Kibana running? Default for start-local is http://localhost:5601"
                ),
            )
        return CheckResult(ok=True, message="200 OK")
    except Exception as err:  # noqa: BLE001
        return CheckResult(
            ok=False,
            message=str(err),
            hint="Is Kibana reachable at KIBANA_URL?",
        )


def ping_agent() -> CheckResult:
    url = os.environ.get("KIBANA_URL")
    key = os.environ.get("ELASTICSEARCH_API_KEY")
    agent_id = os.environ.get("ELASTIC_AGENT_ID")
    if not url or not key or not agent_id:
        return CheckResult(ok=False, message="env vars not set")
    try:
        res = httpx.post(
            f"{url.rstrip('/')}/api/agent_builder/converse",
            headers={
                "Authorization": f"ApiKey {key}",
                "kbn-xsrf": "true",
                "Content-Type": "application/json",
            },
            json={"agent_id": agent_id, "input": "ping"},
            timeout=20.0,
        )
        if res.is_error:
            body = res.text
            if res.status_code == 404:
                hint = (
                    f"Agent '{agent_id}' not found. Did pre-setup.sh complete "
                    "successfully? Check ELASTIC_AGENT_ID matches the agent "
                    "registered in Kibana."
                )
            else:
                hint = f"Response: {body[:200]}"
            return CheckResult(
                ok=False, message=f"HTTP {res.status_code}", hint=hint
            )
        return CheckResult(ok=True, message="agent responded")
    except Exception as err:  # noqa: BLE001
        return CheckResult(
            ok=False,
            message=str(err),
            hint=(
                "Did you run ./es-sandbox/pre-setup.sh? It registers the agent. "
                "And ./es-sandbox/workshop-day-setup.sh on workshop day to wire "
                "up the LLM connector?"
            ),
        )


def ping_github() -> CheckResult:
    key = os.environ.get("GITHUB_API_KEY")
    if not key:
        return CheckResult(
            ok=False,
            message="GITHUB_API_KEY not set",
            hint=(
                "Create a Personal Access Token at https://github.com/settings/tokens "
                "— no scopes needed for public repos"
            ),
        )
    try:
        res = httpx.get(
            "https://api.github.com/rate_limit",
            headers={
                "Authorization": f"token {key}",
                "User-Agent": "deepagent-workshop",
                "Accept": "application/vnd.github+json",
            },
            timeout=8.0,
        )
        if res.is_error:
            return CheckResult(
                ok=False,
                message=f"HTTP {res.status_code}",
                hint="Token may be expired or invalid. Generate a fresh PAT.",
            )
        body = res.json()
        rate = body.get("rate", {})
        return CheckResult(
            ok=True,
            message=f"{rate.get('remaining', '?')}/{rate.get('limit', '?')} req remaining",
        )
    except Exception as err:  # noqa: BLE001
        return CheckResult(ok=False, message=str(err))


def ping_tavily() -> CheckResult:
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        return CheckResult(
            ok=False,
            message="TAVILY_API_KEY not set",
            hint="Sign up free at https://app.tavily.com/ for an API key",
        )
    try:
        res = httpx.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={"api_key": key, "query": "test", "max_results": 1},
            timeout=8.0,
        )
        if res.is_error:
            return CheckResult(
                ok=False,
                message=f"HTTP {res.status_code}",
                hint=f"Response: {res.text[:200]}",
            )
        return CheckResult(ok=True, message="200 OK")
    except Exception as err:  # noqa: BLE001
        return CheckResult(ok=False, message=str(err))


# ---------- check registry ---------------------------------------------

CHECKS: list[Check] = [
    # Env-var checks (instant, no network)
    Check("env: LITELLM_API_KEY", lambda: check_env("LITELLM_API_KEY")),
    Check("env: LITELLM_API_BASE", lambda: check_env("LITELLM_API_BASE")),
    Check("env: ELASTICSEARCH_HOST", lambda: check_env("ELASTICSEARCH_HOST")),
    Check("env: ELASTICSEARCH_API_KEY", lambda: check_env("ELASTICSEARCH_API_KEY")),
    Check("env: KIBANA_URL", lambda: check_env("KIBANA_URL")),
    Check("env: ELASTIC_AGENT_ID", lambda: check_env("ELASTIC_AGENT_ID")),
    Check("env: GITHUB_API_KEY", lambda: check_env("GITHUB_API_KEY")),
    Check("env: TAVILY_API_KEY", lambda: check_env("TAVILY_API_KEY")),
    # Network checks
    Check("LiteLLM proxy reachable", ping_litellm),
    Check("Elasticsearch reachable", ping_es),
    Check("Kibana reachable", ping_kibana),
    Check("Agent Builder agent responds", ping_agent),
    Check("GitHub token works", ping_github),
    Check("Tavily key works", ping_tavily),
]


# ---------- main -------------------------------------------------------


def main() -> int:
    print(f"\n{bold('Verifying workshop setup...')}\n")

    pass_count = 0
    fail_count = 0

    for check in CHECKS:
        sys.stdout.write(f"  {check.name.ljust(38)} ")
        sys.stdout.flush()
        try:
            result = check.run()
        except Exception as err:  # noqa: BLE001
            result = CheckResult(ok=False, message=str(err))

        if result.ok:
            print(f"{green('✓')} {dim(result.message)}")
            pass_count += 1
        else:
            print(f"{red('✗')} {result.message}")
            if result.hint:
                print(f"    {dim(result.hint)}")
            fail_count += 1

    print()
    if fail_count == 0:
        print(green(f"✓ All {pass_count} checks passed. You're ready for the workshop."))
        print()
        return 0

    print(red(f"✗ {fail_count} of {pass_count + fail_count} checks failed."))
    print()
    print("Fix the items above and re-run:")
    print(f"  {bold('python scripts/verify.py')}")
    print()
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:  # noqa: BLE001
        print("\nverify failed unexpectedly:", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

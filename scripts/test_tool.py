"""
Sanity check for Build B (the ask_elastic_agent tool).

Invokes the ask_elastic_agent LangChain tool directly — still no agent
loop, still no orchestrator — and ASSERTS:

    - the tool returns a non-empty string
    - the tool's invocation didn't throw

Run this after you've finished implementing src/tools/ask_elastic_agent.py:

    python scripts/test_tool.py

If you see "Build B sanity check passed", the orchestrator is ready
to dispatch to your elastic subagent.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `from src...` work when running as `python scripts/test_tool.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from src.tools.ask_elastic_agent import ask_elastic_agent  # noqa: E402


GREEN = "\x1b[32m"
RED = "\x1b[31m"
DIM = "\x1b[2m"
BOLD = "\x1b[1m"
RESET = "\x1b[0m"


def main() -> int:
    print("Invoking ask_elastic_agent tool with a test query...\n")

    result = ask_elastic_agent.invoke(
        {"query": "Find technologies similar to 'AI agent orchestration frameworks'"}
    )

    errors: list[str] = []
    if not isinstance(result, str):
        errors.append(f"tool returned a non-string ({type(result).__name__})")
    elif len(result) == 0:
        errors.append("tool returned an empty string")

    if errors:
        print(f"{RED}✗ Build B sanity check FAILED:{RESET}")
        for e in errors:
            print(f"  - {e}")
        print()
        print(f"{DIM}Raw tool output:{RESET}")
        print(f"{DIM}{str(result)[:600]}{RESET}")
        return 1

    print(f"{GREEN}✓ Build B sanity check passed.{RESET}")
    print()
    print(f"{BOLD}Tool output{RESET} ({len(result)} chars):")
    suffix = "…" if len(result) > 500 else ""
    print(f"{result[:500]}{suffix}")
    print()
    print("The orchestrator can now dispatch to your elastic subagent.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as err:  # noqa: BLE001
        print(f"\n{RED}test_tool failed:{RESET}", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

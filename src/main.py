"""
CLI entrypoint for the orchestrator.

Pass a query as command-line arguments; if none, uses a default
question. Prints the final agent reply to stdout.

    python -m src.main "Evaluate elastic/elasticsearch as a search technology"

(For the live workshop UI, run `python -m server.app` instead — that
starts the FastAPI server with the WebSocket-driven activity panel.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `from src...` work when running as `python src/main.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Imported AFTER load_dotenv so module-level env reads succeed.
from src.orchestrator import orchestrator  # noqa: E402


def main() -> None:
    query = (
        " ".join(sys.argv[1:])
        or "Evaluate elastic/elasticsearch — should we recommend it?"
    )

    print(f"Query: {query}\n")
    print("Invoking orchestrator (this routes through subagents)...\n")

    result = orchestrator.invoke({"messages": [{"role": "user", "content": query}]})

    print("\n=== Final reply ===\n")
    last = result["messages"][-1] if result.get("messages") else None
    if last is None:
        print("(no messages)")
    else:
        content = getattr(last, "content", None) or last.get("content")
        if isinstance(content, str):
            print(content)
        else:
            import json

            print(json.dumps(content, indent=2, default=str))

    print(f"\n=== Total messages exchanged: {len(result.get('messages', []))} ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # noqa: BLE001
        print("\nOrchestrator run failed:", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

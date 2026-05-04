"""
End-to-end smoke test for the LLM stack.

Builds a minimal deep agent with one trivial tool and asks it one
question. Validates the full chain in a single shot:

    deepagents → ChatOpenAI → LiteLLM proxy (OpenAI format)
               → Azure /anthropic/v1/messages → Claude Sonnet → back

If this prints a sensible final message, the Python stack is wired
correctly and we can build everything else on top.

Run:
    python scripts/smoke.py

Requires in .env:
    LITELLM_API_KEY   (a master or virtual key from your proxy)
    LITELLM_API_BASE  (https://deepagent-workshop.fly.dev)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make `from src...` work when running as `python scripts/smoke.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

from src.llm import create_llm  # noqa: E402


@tool
def say_hello(name: str) -> str:
    """Greets a person by name. Use this when asked to greet someone.

    Args:
        name: the name of the person to greet
    """
    return f"Hello, {name}! The smoke test reached the tool layer."


def main() -> None:
    print("Building smoke-test agent...")
    agent = create_deep_agent(
        model=create_llm(),
        system_prompt=(
            "You are a friendly test agent. When asked to greet someone, "
            "call the say_hello tool. Keep replies brief."
        ),
        tools=[say_hello],
    )

    print("Invoking with a one-shot prompt...\n")
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Please greet 'workshop' using your tool, then say one "
                        "short sentence about what you did."
                    ),
                }
            ]
        }
    )

    print("=== Full message log ===")
    for msg in result.get("messages", []):
        role = type(msg).__name__
        content = getattr(msg, "content", None)
        if content is None and isinstance(msg, dict):
            content = msg.get("content")
            role = msg.get("role", role)
        if not isinstance(content, str):
            import json

            content = json.dumps(content, default=str, indent=2)
        print(f"\n[{role}]")
        print(content)

    print("\n=== Final agent reply ===")
    last = result["messages"][-1] if result.get("messages") else None
    content = getattr(last, "content", None) if last is not None else None
    if content is None and isinstance(last, dict):
        content = last.get("content")
    print(content if isinstance(content, str) else str(content))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # noqa: BLE001
        print("\nSmoke test failed:", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)

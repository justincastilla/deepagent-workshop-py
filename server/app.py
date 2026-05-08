"""
Workshop web UI server — FastAPI + WebSocket.

Serves a single-page UI that lets attendees submit a research query,
then streams orchestrator activity (subagent dispatches, tool calls,
tool results, final synthesis) over a WebSocket so they can watch the
deep agent unfold in real time.

Architecture:
    GET  /          → static index.html + app.js + styles.css
    WS   /ws        → connect, send {"query": "..."}, receive event stream

Run with:
    python -m server.app
or:
    uvicorn server.app:app --reload --port 3000
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

# Make `from src...` work when running as `python server/app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

# Imported AFTER load_dotenv so module-level env reads succeed.
from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from src.orchestrator import orchestrator  # noqa: E402

PUBLIC_DIR = Path(__file__).parent / "public"

app = FastAPI(title="DevRel-DeepAgent Workshop UI")

# Note: StaticFiles is mounted at "/" at the BOTTOM of this file, AFTER the
# /ws WebSocket route is registered. Mounting "/" early would shadow every
# other route, including the WebSocket upgrade.


# ---------------------------------------------------------------------
# Event filtering — mirrors the JS server's filterEvent + extractOutputText.
# ---------------------------------------------------------------------


def _extract_output_text(output: Any) -> str:
    """Tool outputs come back wrapped in a LangChain message (typically a
    serialized ToolMessage). The actual content the LLM sees lives in
    ``kwargs.content`` (for constructor-serialized messages) or ``.content``
    (for already-instantiated message objects). This unwraps to that string
    so the UI shows the meaningful payload, not the surrounding envelope.
    """
    if output is None:
        return ""
    if isinstance(output, str):
        return output

    # LangChain message objects expose .content directly.
    content = getattr(output, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return _flatten_content_list(content)

    # Constructor-serialized form: {"kwargs": {"content": ...}, ...}
    if isinstance(output, dict):
        kwargs = output.get("kwargs")
        if isinstance(kwargs, dict):
            c = kwargs.get("content")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return _flatten_content_list(c)
        c = output.get("content")
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            return _flatten_content_list(c)

    return json.dumps(output, default=str)


def _flatten_content_list(blocks: list) -> str:
    parts: list[str] = []
    for b in blocks:
        if isinstance(b, str):
            parts.append(b)
        elif isinstance(b, dict) and "text" in b:
            parts.append(str(b["text"]))
        else:
            parts.append(json.dumps(b, default=str))
    return "\n".join(parts)


def _extract_todos(raw_input: Any) -> Optional[list]:
    """`write_todos` is invoked with a `todos` list arg, but the input may
    arrive as a dict, a JSON string, or wrapped in `{"input": "..."}`.
    Returns the unwrapped list, or None if the shape isn't recognized.
    """
    candidate = raw_input
    if isinstance(candidate, dict) and isinstance(candidate.get("input"), str):
        try:
            candidate = json.loads(candidate["input"])
        except json.JSONDecodeError:
            return None
    if isinstance(candidate, str):
        try:
            candidate = json.loads(candidate)
        except json.JSONDecodeError:
            return None
    if isinstance(candidate, dict):
        todos = candidate.get("todos")
        if isinstance(todos, list):
            return todos
    return None


def _filter_event(event: dict) -> Optional[dict]:
    """Decide which streamed events get forwarded to the browser.

    We intentionally drop noisy token-level events and only keep the
    structural ones that explain what the agent is doing.
    """
    name: str = event.get("event", "")
    run_id: Optional[str] = event.get("run_id")
    data: dict = event.get("data") or {}
    tool_name = event.get("name") or "unknown"

    if name == "on_tool_start":
        # `write_todos` gets its own dedicated panel, not the activity stream.
        if tool_name == "write_todos":
            todos = _extract_todos(data.get("input"))
            if todos is not None:
                return {"type": "todos_update", "todos": todos, "runId": run_id}
            return None
        return {
            "type": "tool_start",
            "tool": tool_name,
            "input": data.get("input"),
            "runId": run_id,
        }

    if name == "on_tool_end":
        # Suppress write_todos end — the panel was already updated on start.
        if tool_name == "write_todos":
            return None
        text = _extract_output_text(data.get("output"))
        return {
            "type": "tool_end",
            "tool": tool_name,
            "output_preview": text[:1200],
            "truncated": len(text) > 1200,
            "runId": run_id,
        }

    if name == "on_chat_model_end":
        output = data.get("output")
        # langgraph passes either a message object or a serialized dict.
        content = getattr(output, "content", None)
        tool_calls = getattr(output, "tool_calls", None)
        if isinstance(output, dict):
            content = content if content is not None else output.get("content")
            tool_calls = tool_calls if tool_calls is not None else output.get(
                "tool_calls"
            )

        if isinstance(tool_calls, list) and tool_calls:
            return {
                "type": "model_decision",
                "tool_calls": [
                    {"name": tc.get("name"), "args": tc.get("args")}
                    if isinstance(tc, dict)
                    else {
                        "name": getattr(tc, "name", None),
                        "args": getattr(tc, "args", None),
                    }
                    for tc in tool_calls
                ],
                "runId": run_id,
            }
        if isinstance(content, str) and content.strip():
            return {"type": "message", "content": content, "runId": run_id}
        return None

    return None


# ---------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------


@app.websocket("/ws")
async def ws_handler(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            await _run_query(ws, raw)
    except WebSocketDisconnect:
        return
    except Exception as err:  # noqa: BLE001
        await _send(ws, {"type": "error", "error": str(err)})


async def _run_query(ws: WebSocket, raw: str) -> None:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        await _send(ws, {"type": "error", "error": "invalid JSON"})
        return

    query = str(parsed.get("query", "") if isinstance(parsed, dict) else "").strip()
    if not query:
        await _send(ws, {"type": "error", "error": "missing query"})
        return

    await _send(ws, {"type": "started", "query": query})

    try:
        async for event in orchestrator.astream_events(
            {"messages": [{"role": "user", "content": query}]},
            version="v2",
        ):
            forwarded = _filter_event(event)
            if forwarded is not None:
                await _send(ws, forwarded)
        await _send(ws, {"type": "done"})
    except Exception as err:  # noqa: BLE001
        print(f"orchestrator run failed: {err}")
        await _send(ws, {"type": "error", "error": str(err)})


async def _send(ws: WebSocket, payload: dict) -> None:
    if ws.client_state.name == "CONNECTED":
        await ws.send_text(json.dumps(payload, default=str))


# ---------------------------------------------------------------------
# Static files — mounted LAST so /ws is matched first.
# ---------------------------------------------------------------------

app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "3000"))
    print(f"\n  Workshop web UI: http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()

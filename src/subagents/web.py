"""
Web subagent — web adoption signals specialist.

Calls Tavily's search API for a natural-language query and returns
ranked results (title, URL, content preview, relevance score).

Auth: TAVILY_API_KEY in .env.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import httpx
from langchain_core.tools import tool

from src.utils import safe_slice

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "web.md"
web_prompt = _PROMPT_PATH.read_text(encoding="utf-8")


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing env var {name}. Set it in .env.")
    return v


@tool
def search_adoption_signals(query: str, max_results: int = 5) -> str:
    """Web-search for blog posts, case studies, talks, and job postings about
    a technology. Use a focused natural-language query.

    Args:
        query: the natural-language search query
            (e.g. 'who is using LangGraph in production?')
        max_results: how many results to return (1-10, default 5)
    """
    api_key = _require_env("TAVILY_API_KEY")
    res = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        },
        timeout=30.0,
    )
    if res.is_error:
        raise RuntimeError(f"Tavily error {res.status_code}: {res.text[:400]}")

    data = res.json()
    results = data.get("results", []) or []

    if not results:
        return f'# Web search for "{query}"\n\nNo results found.'

    lines = [f'# Web search for "{query}" ({len(results)} results)', ""]
    for r in results:
        score = r.get("score")
        score_str = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
        cleaned = re.sub(r"\s+", " ", (r.get("content") or "")).strip()
        preview = safe_slice(cleaned, 240)
        lines.append(f"### {r.get('title', '(no title)')}  ·  relevance {score_str}")
        lines.append(f"<{r.get('url', '')}>")
        if preview:
            lines.append("")
            ellipsis = "…" if len(preview) < len(cleaned) else ""
            lines.append(f"> {preview}{ellipsis}")
        lines.append("")
    return "\n".join(lines)


web_subagent = {
    "name": "web-agent",
    "description": (
        "Use to search the web for adoption evidence of a technology: blog "
        "posts, case studies, conference talks, job postings."
    ),
    "system_prompt": web_prompt,
    "tools": [search_adoption_signals],
}

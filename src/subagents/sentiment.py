"""
Sentiment subagent — community sentiment specialist.

Pulls the most-recent N issues from a GitHub repo (filtering out PRs,
which the same endpoint returns) and hands the title + body preview
back to the subagent's LLM for thematic analysis.

Auth: GITHUB_API_KEY in .env.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.tools import tool

from src.tools.github import github_get
from src.utils import safe_slice

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "sentiment.md"
sentiment_prompt = _PROMPT_PATH.read_text(encoding="utf-8")


@tool
def fetch_recent_issues(owner: str, repo: str, limit: int = 10) -> str:
    """Fetch the most-recent N issues for a GitHub repo (excluding pull requests).

    Returns titles, body previews, labels, and comment counts as Markdown.

    Args:
        owner: repo owner / org name
        repo: repo name
        limit: how many issues to fetch (1-30, default 10)
    """
    lim = max(1, min(30, limit))
    try:
        res = github_get(
            f"/repos/{owner}/{repo}/issues?per_page={lim}&state=all&sort=created&direction=desc"
        )
    except RuntimeError as e:
        return f"# Recent issues for {owner}/{repo}\n\nGitHub request failed: {e}"
    raw = res.json()
    if not isinstance(raw, list):
        # Defensive: a 200 with a {"message": "..."} body would otherwise
        # cause `for i in raw` to iterate dict keys (strings), and
        # `i.get(...)` would explode with `'str' object has no attribute 'get'`.
        msg = raw.get("message") if isinstance(raw, dict) else str(raw)[:200]
        return (
            f"# Recent issues for {owner}/{repo}\n\n"
            f"Could not fetch issues — GitHub returned: {msg}"
        )

    # The issues endpoint returns PRs too — filter them out.
    issues = []
    for i in raw:
        if not isinstance(i, dict):
            continue
        if i.get("pull_request"):
            continue
        body = re.sub(r"\s+", " ", (i.get("body") or "")).strip()
        issues.append(
            {
                "number": i["number"],
                "title": i["title"],
                "state": i["state"],
                "body_preview": safe_slice(body, 400),
                "labels": [lbl["name"] for lbl in i.get("labels", [])],
                "comments": i.get("comments", 0),
                "created_at": i["created_at"],
                "url": i["html_url"],
            }
        )

    if not issues:
        return f"# Recent issues for {owner}/{repo}\n\nNo recent issues found."

    lines = [f"# Recent issues for {owner}/{repo} ({len(issues)} found)", ""]
    for i in issues:
        lines.append(f"### #{i['number']} · {i['title']}")
        lines.append(
            f"- **State:** {i['state']}  ·  **Comments:** {i['comments']}  ·  "
            f"**Created:** {i['created_at'][:10]}"
        )
        if i["labels"]:
            lines.append(f"- **Labels:** {', '.join(i['labels'])}")
        lines.append(f"- **URL:** {i['url']}")
        if i["body_preview"]:
            sliced = safe_slice(i["body_preview"], 240)
            trimmed = sliced + "…" if len(sliced) < len(i["body_preview"]) else sliced
            lines.append("")
            lines.append(f"> {trimmed}")
        lines.append("")
    return "\n".join(lines)


sentiment_subagent = {
    "name": "sentiment-agent",
    "description": (
        "Use to analyze community sentiment for a GitHub repo: pain points, "
        "praise, recurring themes from recent issues."
    ),
    "system_prompt": sentiment_prompt,
    "tools": [fetch_recent_issues],
}

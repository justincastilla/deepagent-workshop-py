"""
Metrics subagent — GitHub repo metrics specialist.

Calls the GitHub REST API for an owner/repo pair and returns:
  - stars, forks, watchers, open_issues
  - contributors (counted via Link-header pagination trick)
  - commits in the last 7 days

Auth: GITHUB_API_KEY (PAT) in .env.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from langchain_core.tools import tool

from src.tools.github import github_get, total_from_link_header

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "metrics.md"
metrics_prompt = _PROMPT_PATH.read_text(encoding="utf-8")


@tool
def fetch_repo_metrics(owner: str, repo: str) -> str:
    """Fetch GitHub repository metrics: stars, forks, watchers, contributors,
    commits in the last 7 days, open issues count.

    Args:
        owner: repo owner / org name (e.g. 'elastic')
        repo: repo name (e.g. 'elasticsearch')
    """
    try:
        # 1) Repo info — single call, gets stars/forks/watchers/open_issues.
        repo_data = github_get(f"/repos/{owner}/{repo}").json()
        if not isinstance(repo_data, dict) or "stargazers_count" not in repo_data:
            return (
                f"# Metrics for {owner}/{repo}\n\n"
                f"Could not fetch repo info — GitHub returned an unexpected payload "
                f"(no `stargazers_count`). Double-check the owner and repo names."
            )

        # 2) Contributor count — via Link-header pagination trick. Cheap.
        contrib_res = github_get(
            f"/repos/{owner}/{repo}/contributors?per_page=1&anon=1"
        )
        contributors = total_from_link_header(contrib_res.headers.get("Link"))
        if contributors is None:
            body = contrib_res.json()
            contributors = len(body) if isinstance(body, list) else 0

        # 3) Commits in the last 7 days.
        since = (dt.datetime.utcnow() - dt.timedelta(days=7)).isoformat() + "Z"
        commits_res = github_get(
            f"/repos/{owner}/{repo}/commits?since={since}&per_page=100"
        )
        commits = commits_res.json()
        commits_last_week = len(commits) if isinstance(commits, list) else 0
    except RuntimeError as e:
        return f"# Metrics for {owner}/{repo}\n\nGitHub request failed: {e}"

    # Markdown formatting — readable for both the LLM AND the human
    # watching the activity panel. .get() with defaults so a partial
    # response degrades gracefully instead of raising KeyError.
    fmt = lambda n: f"{n:,}"
    pushed_at = repo_data.get("pushed_at") or ""
    return "\n".join(
        [
            f"# Metrics for {owner}/{repo}",
            "",
            f"- **Stars:** {fmt(repo_data.get('stargazers_count', 0))}",
            f"- **Forks:** {fmt(repo_data.get('forks_count', 0))}",
            f"- **Watchers:** {fmt(repo_data.get('subscribers_count', 0))}",
            f"- **Contributors:** {fmt(contributors)}",
            f"- **Open issues:** {fmt(repo_data.get('open_issues_count', 0))}",
            f"- **Commits in last 7 days:** {commits_last_week}",
            f"- **Last push:** {pushed_at[:10] if pushed_at else 'unknown'}",
        ]
    )


metrics_subagent = {
    "name": "metrics-agent",
    "description": (
        "Use to fetch GitHub repository metrics: stars, forks, contributors, "
        "commit velocity. Pass an owner/repo pair."
    ),
    "system_prompt": metrics_prompt,
    "tools": [fetch_repo_metrics],
}

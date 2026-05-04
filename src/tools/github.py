"""
Shared GitHub API helper.

Used by the metrics and sentiment subagents. Wraps httpx with auth +
the Accept/User-Agent headers GitHub expects.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import httpx


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing env var {name}. Set it in .env.")
    return v


def github_get(path: str) -> httpx.Response:
    """Authenticated GET against api.github.com.

    Returns the raw Response so callers can read both the body and the
    headers (the Link header carries total counts via pagination).
    """
    token = _require_env("GITHUB_API_KEY")
    url = f"https://api.github.com{path}"
    res = httpx.get(
        url,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "deepagent-workshop",
        },
        timeout=30.0,
    )
    if res.is_error:
        raise RuntimeError(
            f"GitHub API error {res.status_code} on {path}: {res.text[:400]}"
        )
    return res


def total_from_link_header(link_header: Optional[str]) -> Optional[int]:
    """Pull a 'total count' from a paginated GitHub endpoint by reading the
    `rel="last"` page number from the Link header.

    Many endpoints (like /contributors) don't return a count directly, so the
    trick is to call with `per_page=1` and parse the last-page number.
    """
    if not link_header:
        return None
    match = re.search(r'<[^>]*[?&]page=(\d+)>;\s*rel="last"', link_header)
    return int(match.group(1)) if match else None

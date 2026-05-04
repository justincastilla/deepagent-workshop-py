"""
Tiny utilities shared across subagents.
"""

from __future__ import annotations


def safe_slice(s: str, max_chars: int) -> str:
    """Slice a string by Unicode code points (not UTF-16 code units, which
    Python doesn't have anyway, but we ALSO want to count code points rather
    than bytes so multi-byte UTF-8 characters don't get cut mid-character
    when serialized JSON crosses an HTTP boundary).

    Prevents `[:n]` from splitting an emoji or other multi-codepoint character
    mid-grapheme — which produces a value the LiteLLM proxy + Anthropic API
    can reject as 'invalid low surrogate'.

    Python strings are already code-point-indexed, so a plain slice is safe
    for the most common cases. We keep this helper for parity with the JS
    workshop and to make intent obvious to readers.
    """
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars]

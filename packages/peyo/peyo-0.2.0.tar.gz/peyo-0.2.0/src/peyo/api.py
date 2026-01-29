"""Stable public API.

Entry points:
- yoify(text, mode='safe') -> str
- lint(text, mode='safe', group_by_words=False) -> list[dict]

Aliases:
- restore == yoify
- yo == yoify

Default behaviour is conservative (mode='safe'), matching eyo's philosophy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from .builtins import not_safe_eyo, safe_eyo


Mode = Literal["safe", "not_safe"]


def _normalize_mode(mode: str, safe: Optional[bool]) -> Mode:
    """Normalize mode selection.

    `safe` is accepted for compatibility with common patterns (deprecated).
    """

    if safe is not None:
        mode = "safe" if safe else "not_safe"

    m = (mode or "safe").strip().lower()
    if m in ("safe", "s"):
        return "safe"
    if m in ("not_safe", "notsafe", "unsafe", "not-safe", "ns"):
        return "not_safe"
    raise ValueError("mode must be 'safe' or 'not_safe'")


def yoify(text: str, mode: str = "safe", safe: Optional[bool] = None) -> str:
    """Restore 'ё' in Russian text.

    Designed to be safely callable as `yoify(text)` with no kwargs.

    Args:
        text: input text
        mode: 'safe' (default) or 'not_safe'
        safe: deprecated boolean switch; if provided overrides `mode`
    """

    m = _normalize_mode(mode, safe)
    engine = safe_eyo if m == "safe" else not_safe_eyo
    return engine.restore(text)


def lint(
    text: str,
    mode: str = "safe",
    *,
    group_by_words: bool = False,
    safe: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """Return possible replacements without modifying the text."""

    m = _normalize_mode(mode, safe)
    engine = safe_eyo if m == "safe" else not_safe_eyo
    return engine.lint(text, group_by_words=group_by_words)


# Friendly aliases for "universal" callers.
restore = yoify
yo = yoify

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Any, Dict, List

from .dictionary import Dictionary


# Mirrors eyo-kernel/src/eyo.ts
_PUNCTUATION = r"[{}()[\\]|<>=\\_\"'«»„“#$^%&*+-:;.,?!]"
_REGEXP = re.compile(
    r"([А-ЯЁа-яё])[а-яё]+(?![а-яё]|\.[ \u00A0\t]+([а-яё]|[А-ЯЁ]{2}|" + _PUNCTUATION + r")|\." + _PUNCTUATION + r")",
    flags=re.UNICODE,
)


@dataclass(frozen=True)
class Position:
    line: int
    column: int
    index: int


@dataclass
class Replacement:
    before: str
    after: str
    position: List[Position]


class Eyo:
    """Python port of eyo-kernel Eyo class.

    - restore(text) -> str
    - lint(text, group_by_words=False) -> list[dict]

    The API mirrors the JS behavior closely (positions are 1-based for line/column).
    """

    def __init__(self) -> None:
        self.dictionary = Dictionary()

    def lint(self, text: str, group_by_words: bool = False) -> List[Dict[str, Any]]:
        replacements: List[Replacement] = []

        if not text or not self._has_eyo(text):
            return []

        for m in _REGEXP.finditer(text):
            word_e = m.group(0)
            word_yo = self.dictionary.restore_word(word_e)
            if word_yo != word_e:
                replacements.append(
                    Replacement(
                        before=word_e,
                        after=word_yo,
                        position=[self._get_position(text, m.start())],
                    )
                )

        if group_by_words:
            replacements.sort(key=cmp_to_key(_cmp_replacements))
            replacements = self._del_duplicates(replacements)

        # Return plain dicts to keep it JSON-friendly.
        return [
            {
                "before": r.before,
                "after": r.after,
                "position": [p.__dict__ for p in r.position],
            }
            for r in replacements
        ]

    def restore(self, text: str) -> str:
        if not text or not self._has_eyo(text):
            return text or ""

        def repl(m: re.Match[str]) -> str:
            word_e = m.group(0)
            word_yo = self.dictionary.restore_word(word_e)
            return word_yo if word_yo != word_e else word_e

        return _REGEXP.sub(repl, text)

    @staticmethod
    def _has_eyo(text: str) -> bool:
        return re.search(r"[ЕЁеё]", text) is not None

    @staticmethod
    def _get_position(text: str, index: int) -> Position:
        # Matches JS: text.substr(0, index).split(/\r?\n/)
        buf = re.split(r"\r?\n", text[:index])
        return Position(line=len(buf), column=len(buf[-1]) + 1, index=index)

    @staticmethod
    def _del_duplicates(replacements: List[Replacement]) -> List[Replacement]:
        positions: Dict[str, List[Position]] = {}
        for item in replacements:
            positions.setdefault(item.before, []).extend(item.position)

        added: Dict[str, bool] = {}
        result: List[Replacement] = []
        for item in replacements:
            if not added.get(item.before):
                result.append(
                    Replacement(
                        before=item.before,
                        after=item.after,
                        position=positions[item.before],
                    )
                )
                added[item.before] = True
        return result


def _cmp_replacements(a: Replacement, b: Replacement) -> int:
    """Replicates Eyo.sort comparator from JS."""

    a_before = a.before
    b_before = b.before
    a_lower = a_before.lower()
    b_lower = b_before.lower()

    if a_before[0] != b_before[0] and a_lower[0] == b_lower[0]:
        if a_before > b_before:
            return 1
        return -1

    if a_lower > b_lower:
        return 1
    if a_lower < b_lower:
        return -1
    return 0

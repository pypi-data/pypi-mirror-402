from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Union


def _replace_yo(word: str) -> str:
    # JS version: word.replace(/Ё/g,'Е').replace(/ё/g,'е')
    return word.replace("Ё", "Е").replace("ё", "е")


def _capitalize(text: str) -> str:
    return (text[:1].upper() + text[1:]) if text else text


@dataclass
class Dictionary:
    _dict: Dict[str, str]

    def __init__(self) -> None:
        self._dict = {}

    def clear(self) -> None:
        self._dict = {}

    def restore_word(self, word: str) -> str:
        return self._dict.get(_replace_yo(word), word)

    def add_word(self, raw_word: str) -> None:
        word = raw_word
        if "#" in raw_word:
            word = raw_word.split("#", 1)[0].strip()

        if not word:
            return

        if "(" in word:
            # JS: word.split(/[(|)]/)
            parts = re.split(r"[()|]", word)
            # JS loop: for i=1, len=parts.length-1; i<len; i++
            for i in range(1, max(len(parts) - 1, 1)):
                self._add_word_inner(parts[0] + parts[i])
        else:
            self._add_word_inner(word)

    def remove_word(self, word: str) -> None:
        word_e = _replace_yo(word)
        self._dict.pop(word_e, None)

        # JS: if word.search(/^[А-ЯЁ]/) === -1
        if not re.search(r"^[А-ЯЁ]", word):
            self._dict.pop(_capitalize(word_e), None)

    def set(self, data: Union[str, Iterable[str], None]) -> None:
        self.clear()
        if not data:
            return

        if isinstance(data, str):
            buffer = data.strip().splitlines()
        else:
            buffer = list(data)

        for w in buffer:
            self.add_word(w)

    def get(self) -> Dict[str, str]:
        return self._dict

    def _add_word_inner(self, word: str) -> None:
        # Leading underscore: only lowercase usage, do not add capitalized form
        has_underscore = word.startswith("_")
        word = re.sub(r"^_", "", word)
        if not word:
            return

        key = _replace_yo(word)
        self._dict[key] = word

        # JS: if word.search(/^[А-ЯЁ]/) === -1 && !hasUnderscore
        if not re.search(r"^[А-ЯЁ]", word) and not has_underscore:
            self._dict[_capitalize(key)] = _capitalize(word)

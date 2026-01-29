from __future__ import annotations

from importlib.resources import files

from .eyo import Eyo


def _read_data(name: str) -> str:
    return files("peyo").joinpath("data", name).read_text(encoding="utf-8")


safe_dictionary: str = _read_data("safe.txt")
not_safe_dictionary: str = _read_data("not_safe.txt")

safe_eyo = Eyo()
safe_eyo.dictionary.set(safe_dictionary)

not_safe_eyo = Eyo()
not_safe_eyo.dictionary.set(not_safe_dictionary)

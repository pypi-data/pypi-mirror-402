# peyo

Pure-Python port of the `eyo-kernel` yoification engine.

## Quickstart

```python
from peyo import safe_eyo, not_safe_eyo

print(safe_eyo.restore("Ежик и елка"))
print(not_safe_eyo.restore("все"))
```

- `safe_eyo` uses the `dictionary/safe.txt` from `eyo-kernel`.
- `not_safe_eyo` uses `dictionary/not_safe.txt`.

API:
- `Eyo.restore(text) -> str`
- `Eyo.lint(text, group_by_words=False) -> list[dict]`

Dictionaries:
- `Eyo().dictionary.set(str_or_lines)`
- `Eyo().dictionary.add_word(line)`
- `Eyo().dictionary.remove_word(word)`

## Attribution

This project is a Python port of **eyo-kernel** by Denis Seleznev and uses the upstream dictionaries.
The original project is MIT-licensed; see `LICENSE`.


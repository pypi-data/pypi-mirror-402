# peyo

Pure-Python port of **eyo-kernel** (dictionary-based Russian “ё” restoration / yoification).  
No Node.js required.

🇷🇺 Русская документация: [README.ru.md](README.ru.md)

## Install

```bash
pip install peyo
```

## Quickstart

```python
import peyo

text = "«Лед тронулся, господа присяжные заседатели!»"
print(peyo.yoify(text))
# -> «Лёд тронулся, господа присяжные заседатели!»
```

## Modes

Yoification in Russian is ambiguous (e.g. `все/всё`, `осел/осёл`).  
So `peyo` supports two modes:

- `mode="safe"` (default): conservative replacements, minimal false positives
- `mode="not_safe"`: more aggressive, can produce mistakes

```python
import peyo

print(peyo.yoify("Ежик и елка"))
# -> "Ёжик и ёлка"

print(peyo.yoify("все", mode="safe"))
# -> "все"     (safe avoids ambiguous cases)

print(peyo.yoify("все", mode="not_safe"))
# -> "всё"     (more aggressive)
```

## API

### `peyo.yoify(text: str, mode: str = "safe") -> str`
Main function. Stable public API.

Aliases:
- `peyo.restore(...)`
- `peyo.yo(...)`

### `peyo.lint(text: str, mode: str = "safe", group_by_words: bool = False) -> list[dict]`
Returns a list of suggested replacements (does not modify the text).

Example output item:
```json
{
  "before": "Лед",
  "after": "Лёд",
  "position": [{"line": 1, "column": 2, "index": 1}]
}
```

## Notes

- This library is dictionary-based (no ML, no true contextual disambiguation).
- `safe` mode is recommended for fully automatic pipelines.
- For maximum quality you typically use `safe` restore + manual review of `not_safe` candidates.

## Attribution / License

This project is a Python port of **eyo-kernel** by Denis Seleznev and uses upstream dictionaries.  
The upstream project is MIT-licensed. See `LICENSE`.

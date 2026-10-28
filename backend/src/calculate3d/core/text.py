"""Name rules shared by modules (ADR 0006): trim, casefolded key, search, Ukrainian order.

SQLite folds case and sorts only ASCII, so all of this lives in Python.
"""

UKRAINIAN_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
_UK_RANK = {letter: rank for rank, letter in enumerate(UKRAINIAN_ALPHABET)}

# Script groups: names starting with a Latin letter first, then Cyrillic, then anything else.
_LATIN, _CYRILLIC, _OTHER = 0, 1, 2


def normalize_name(raw: str) -> str:
    return raw.strip()


def name_key(name: str) -> str:
    return normalize_name(name).casefold()


def contains(name: str, query: str) -> bool:
    return name_key(query) in name_key(name)


def _script(char: str) -> int:
    if "a" <= char <= "z":
        return _LATIN
    if "Ѐ" <= char <= "ӿ":
        return _CYRILLIC
    return _OTHER


def _char_key(char: str) -> tuple[int, int]:
    script = _script(char)
    if script == _CYRILLIC:
        # Letters outside the Ukrainian alphabet sort after «я».
        return (script, _UK_RANK.get(char, len(UKRAINIAN_ALPHABET) + ord(char)))
    return (script, ord(char))


def sort_key(name: str) -> tuple[int, tuple[tuple[int, int], ...], str]:
    key = name_key(name)
    group = _script(key[0]) if key and key[0].isalpha() else _OTHER
    return (group, tuple(_char_key(c) for c in key), name)

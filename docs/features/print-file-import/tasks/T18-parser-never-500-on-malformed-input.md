---
id: T18
title: "Парсер: будь-який пошкоджений вміст архіву → importing.corrupted_file, ніколи не 500"
layer: "app"
deps: ["T3", "T4"]
acs: ["AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/tests/fixtures/slicer/bad_files.py", "backend/tests/integration/test_importing_bad_files.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T18 — Парсер: будь-який пошкоджений вміст архіву → importing.corrupted_file, ніколи не 500

## Why

Review F1–F3: `int()` на рядку >4300 цифр (`ValueError`), невідоме `encoding=` у XML (`LookupError`) і UTF-8-прапор локального заголовка ZIP з невалідним іменем (`UnicodeDecodeError`) виходять повз `ParseError` → `500 internal_error`, що порушує AC-13 / SAD QG-2, а traceback логує рядок із файлу (SAD §8 Logging). Джерело: [review 2026-11-10](../_review/review-2026-11-10.md).

## What

- `parser.py:199-202` `_positive_int`: відхиляти рядки довші за 9 цифр до `int()` → `ParseError(CORRUPTED_FILE)`.
- `parser.py:159-163`: ловити `(ET.ParseError, LookupError, ValueError)` → `ParseError(CORRUPTED_FILE)`.
- `parser.py:148-153`: додати `ValueError` (покриває `UnicodeDecodeError`) у кортеж винятків `archive.open`.
- `tests/fixtures/slicer/bad_files.py`: три нові випадки (довге число в `index`/`filament id`, bogus encoding, local-header bad-UTF-8).

## Definition of Done

> Три нові bad-file випадки повертають 422 importing.corrupted_file (тест через TestClient), жоден не дає 500, а make api-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений

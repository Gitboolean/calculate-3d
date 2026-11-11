---
id: T23
title: "Парсер: межа реального central directory, version > 6.3 і лише ASCII-цифри → importing.corrupted_file"
layer: "app"
deps: ["T19"]
acs: ["AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/src/calculate3d/modules/importing/normalize.py", "backend/tests/fixtures/slicer/bad_files.py", "backend/tests/unit/test_importing_archive_budget.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "todo"
---

# T23 — Парсер: межа реального central directory, version > 6.3 і лише ASCII-цифри → importing.corrupted_file

## Why

Re-review R1: `_check_central_directory` (`parser.py:192`) перевіряє оголошений у EOCD count, а `zipfile` читає CD за `size_cd` (`while total < size_cd`); межа `MAX_ENTRIES * MAX_CD_RECORD_BYTES` ≈ 655 МБ ніколи не спрацьовує → count=1 над CD 94 МБ дає RSS ~930 МБ (SAD §7 ≈132 МБ). R2: `NotImplementedError("zip file version 6.4")` з `ZipFile.__init__` не в except (`parser.py:125`) → 500 (QG-2). Q8: `\d` у `normalize.py:16-17` приймає не-ASCII цифри (SAD §8 «plain decimals»). Джерело: [review 2026-11-10 r2](../_review/review-2026-11-10-r2.md).

## What

- Обмежити те, що реально розбере `zipfile`: пройти записи CD через `struct` від `eocd − size_cd` (Zip64 record, коли є locator) і відмовити на MAX_ENTRIES+1, або жорстко обмежити `size_cd` (напр. ≤ MAX_ENTRIES × 1024).
- Додати `NotImplementedError` до except на `parser.py:125` → CORRUPTED_FILE.
- `_GRAMS`/`_SECONDS`: `[0-9]` або `re.ASCII`.
- Три нові bad-file випадки; CD-flood — у тест, де конструювання ZipFile заборонене.

## Definition of Done

> Bad-file випадки cd_flood_small_declared_count (CD > 10 000 записів при EOCD count ≤ 10 000), cd_extract_version_unsupported і non_ascii_digits_in_usage дають 422 importing.corrupted_file; тест бюджету показує, що ZipFile не будується для CD-flood; make api-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений

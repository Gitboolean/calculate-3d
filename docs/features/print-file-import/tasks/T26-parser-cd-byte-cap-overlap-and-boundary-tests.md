---
id: T26
title: "Парсер: межа байтів central directory, відмова на overlapped-записах і тести меж"
layer: "app"
deps: ["T23"]
acs: ["AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/tests/fixtures/slicer/bad_files.py", "backend/tests/unit/test_importing_archive_budget.py", "backend/tests/unit/test_importing_parser.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T26 — Парсер: межа байтів central directory, відмова на overlapped-записах і тести меж

## Why

Re-review r3. S1: T23 обмежив кількість записів CD (10 000), але не байти — `zipfile` читає весь
`size_cd` і тримає name/extra/comment кожного запису (≤ 64 КБ), тож 1 509 записів з іменем 65 535 Б у
тілі 99 МБ дають пік +298 МБ (SAD §7 ≈ 132 МБ). S3: `_SECONDS` з `\d` не ловить жоден тест. S6: гілка
Zip64 `location = reloff` (`parser.py:194-195`) без тесту, її мутант пропускає flood на 12 005 записів.
S7: немає тесту, що рівно 10 000 записів приймається. S8: `ZipFile.open` друкує в stderr
`Overlapped entries: '<ім'я з файлу>'` і продовжує (SAD §8 Logging). Джерело:
[review 2026-11-11 r3](../_review/review-2026-11-11-r3.md).

## What

- `MAX_CD_BYTES` (≈ 4 МБ; реальні CD 1–5 КБ): `_check_central_directory` відмовляє на `size_cd > MAX_CD_BYTES` → `corrupted_file`.
- Перед `open` відмовити, якщо два записи `infolist()` мають однаковий `header_offset` → `corrupted_file` (без `warnings.catch_warnings` — глобальний стан, threadpool).
- Bad-file випадки: `cd_fat_records`, `cd_oversized_within_entry_limit`, `cd_flood_zip64_extensible_data` (у `OVER_LIMIT_CASES` і в тест «plain zipfile accepts»), `non_ascii_digits_in_print_time`, `overlapped_entries`.
- Unit-тест: архів рівно з 10 000 записів проходить крок 0 (не `corrupted_file`).

## Definition of Done

> Bad-file випадки cd_fat_records, cd_oversized_within_entry_limit, cd_flood_zip64_extensible_data, non_ascii_digits_in_print_time і overlapped_entries дають 422 importing.corrupted_file, а ZipFile не будується для CD-випадків; архів рівно з 10 000 записів не відхиляється як corrupted_file; кожен тест червоніє при відкаті свого фіксу; make api-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений

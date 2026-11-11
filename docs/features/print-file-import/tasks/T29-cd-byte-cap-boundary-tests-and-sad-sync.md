---
id: T29
title: "Межа байтів central directory у тестах і синхронізація SAD з новими правилами архіву"
layer: "app"
deps: ["T26"]
acs: ["AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/tests/fixtures/slicer/bad_files.py", "backend/tests/unit/test_importing_archive_budget.py", "backend/tests/unit/test_slicer_bad_files.py", "docs/features/print-file-import/sad.md"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T29 — Межа байтів central directory у тестах і синхронізація SAD з новими правилами архіву

## Why

Re-review r4. R7a: мутант `size >= MAX_CD_BYTES` (`parser.py:203`) проходить усі тести — фікстури
6,07 / 6,56 МБ, guard (`test_slicer_bad_files.py:126`) порівнює з `4 * 1024 * 1024`, а не з
`MAX_CD_BYTES = 4_000_000`; `_cd_record` з `header_offset=0` робить ці фікстури ще й overlapped.
R8: SAD §8 (`sad.md:542`) і QG-2 (`:579`) не називають ліміт CD 4 000 000 байт і відмову на двох
записах над одним локальним заголовком; §7 (`:532`) не рахує запас на CD (≈ +12 МБ); docstring
`_check_central_directory` (`parser.py:176`) і назва тесту (`test_importing_archive_budget.py:31`)
кажуть лише про кількість записів. Джерело: [review 2026-11-11 r4](../_review/review-2026-11-11-r4.md).

## What

- Тести: валідний архів з CD рівно `MAX_CD_BYTES` байт (різні `header_offset`, доповнення через `ZipInfo.comment`) проходить межі архіву; `MAX_CD_BYTES + 1` → `importing.corrupted_file` без побудови `ZipFile`; guard порівнює з `parser.MAX_CD_BYTES`; byte-cap фікстури отримують різні `header_offset`.
- `sad.md`: §8 «Межі читання архіву» + QG-2 — ліміт CD ≤ 4 000 000 байт і «два записи над одним локальним заголовком → файл пошкоджений»; §7 — запас на CD у сумі піку.
- Docstring «entry count or byte size»; тест → `test_over_limit_central_directory_is_rejected_before_zipfile_is_constructed`.

## Definition of Done

> Accept-тест рівно на MAX_CD_BYTES і reject-тест на MAX_CD_BYTES + 1 червоніють на мутантах `>=` і на підвищеному ліміті; byte-cap фікстури не overlapped; SAD §7/§8/§10 називають обидва нові правила; make api-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений

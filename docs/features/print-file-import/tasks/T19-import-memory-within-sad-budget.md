---
id: T19
title: "Пам'ять імпорту в бюджеті SAD §7: межа central directory до ZipFile і один буфер тіла"
layer: "infra"
deps: ["T8", "T18"]
acs: ["AC-13"]
files_hint: ["backend/src/calculate3d/modules/importing/parser.py", "backend/src/calculate3d/modules/importing/router.py", "backend/tests/fixtures/slicer/bad_files.py", "backend/tests/integration/test_nfr_import_latency.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T19 — Пам'ять імпорту в бюджеті SAD §7: межа central directory до ZipFile і один буфер тіла

## Why

Review Q1–Q2: `zipfile.ZipFile()` будує всі `ZipInfo` до перевірки `MAX_ENTRIES` (95 МБ з 1,8 млн порожніх записів → ~860 МБ RSS, 4,5 с), а `bytes(body)` у роутері копіює 100-МБ `bytearray` (пік ~200 МБ) — проти ≈ 132 МБ у SAD §7/§11. Джерело: [review 2026-11-10](../_review/review-2026-11-10.md).

## What

- `parser.py:119-128`: перед `ZipFile` прочитати EOCD (і Zip64 EOCD) і відхилити, якщо кількість записів > `MAX_ENTRIES` або розмір central directory > межі, прив'язаної до `MAX_ENTRIES` → `importing.corrupted_file`.
- `router.py:37-42`: збирати тіло в один `io.BytesIO` (або `b"".join` зі звільненням списку) і передавати парсеру без другої копії.
- Новий bad-file випадок «величезний central directory» з асерцією часу (< NFR) і відмовою до розбору всього каталогу.

## Definition of Done

> Тест «величезний central directory» відхиляється за обмежений час без побудови всіх ZipInfo, тіло в роутері тримається одним буфером, а make api-check зелений.

- [ ] Спершу червоний тест, що відтворює знахідку
- [ ] `make check` зелений

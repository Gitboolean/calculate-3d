---
id: T34
title: "Межа тіла рівно 100 МБ приймається — функціональний тест, що не пропускається на CI"
layer: "tests"
deps: ["T19"]
acs: ["AC-13"]
files_hint: ["backend/tests/integration/test_importing_api.py", "backend/src/calculate3d/modules/importing/router.py"]
owner: "Anton Pohorielov"
estimate: "XS"
status: "todo"
---

# T34 — Межа тіла рівно 100 МБ приймається — функціональний тест, що не пропускається на CI

## Why

Re-review r8, R17. PRD §6 «Межа розміру ≤ 100 МБ»: тіло рівно 100 000 000 байт має прийматися.
Це перевіряє лише тест латентності (`test_nfr_import_latency.py:55-61`), а він позначений
`@on_ci` (`test_nfr_latency.py:37-39`) і на CI пропускається. Функціональні тести
(`test_importing_api.py:82,90,102`) надсилають лише `MAX_BODY + 1`. Мутант r8 — обидві перевірки
`> MAX_BODY_BYTES` у `router.py:35,40` → `>=` — з `CI=1` виживає (675 passed, 9 skipped).
Джерело: [review 2026-11-11 r8](../_review/review-2026-11-11-r8.md).

## What

- Тест у `test_importing_api.py`: `bytes(MAX_BODY)` з Content-Length і chunked → 422
  `importing.not_slicer_project` (відмова парсера), не 413. Без `@on_ci`.

## Definition of Done

> Межу 100 МБ на обох шляхах читання тіла (Content-Length і chunked) перевіряє тест, що працює на
> CI; мутант `>` → `>=` червоніє з `CI=1`; `make check` зелений.

- [ ] Спершу тест, що вбиває мутант (на поточному коді зелений — це тест на межу, не на баг)
- [ ] `make check` зелений

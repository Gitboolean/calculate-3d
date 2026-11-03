---
id: T2
title: "Додати core/text.py (trim, name_key, пошук, український порядок) і поля-розширення AppError"
layer: "domain"
deps: []
acs: ["AC-02", "AC-03", "AC-09", "AC-11", "AC-12"]
files_hint: ["backend/src/calculate3d/core/text.py", "backend/src/calculate3d/core/errors.py", "backend/tests/unit/test_text.py", "backend/tests/integration/test_errors.py"]
owner: "Anton Pohorielov"
estimate: "M"
status: "done"
---

# T2 — Додати core/text.py (trim, name_key, пошук, український порядок) і поля-розширення AppError

## Why

[ADR-0006](../adr/0006-enforce-name-uniqueness-via-casefolded-name-key.md) переносить унікальність, пошук і сортування назв у Python; [sad.md](../sad.md) §8 «Error handling» додає `field` / `items` / `missing` у problem+json, а без них UI не зможе підсвітити поле, назвати вироби для AC-03 чи сказати, яких налаштувань бракує (AC-09). Критерії: AC-02, AC-03, AC-09, AC-11, AC-12 у [PRD §5](../PRD.md).

## What

- `core/text.py`: `normalize_name(s)` (trim), `name_key(s)` (`casefold`), `matches(name, query)` (підрядок у casefold), `sort_key(name)` — спершу латиниця, потім кирилиця за українською абеткою (г < ґ, е < є, и < і < ї < й), без урахування регістру.
- `AppError` отримує необов'язкові `field`, `items`, `missing`; `_app_error` передає непорожні в `problem(**extra)`.

## Definition of Done

- [ ] `tests/unit/test_text.py`: приклад сортування з AC-12, trim («PETG чорний » = «PETG чорний»), casefold («petg чорний»), пошук «тризуб» у «Брелок-тризуб».
- [ ] `tests/integration/test_errors.py`: `AppError(..., items=[...])` → тіло має `items`; без розширень тіло не змінилося.
- [ ] `make api-check` зелений.

## Notes

- **Blocked by:** —.
- Чиста логіка без I/O — стартує паралельно з T1/T3/T5/T13.

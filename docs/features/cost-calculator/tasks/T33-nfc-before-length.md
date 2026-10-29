---
id: T33
title: "Нормалізувати ім'я (NFC) до перевірки довжини, щоб довге після NFC ім'я давало 422"
layer: "app"
deps: []
acs: ["AC-02", "AC-11"]
files_hint: ["backend/src/calculate3d/core/schemas.py", "backend/src/calculate3d/core/text.py", "backend/tests/integration/test_input_bounds.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T33 — Нормалізувати ім'я (NFC) до перевірки довжини, щоб довге після NFC ім'я давало 422

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-02, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] Name у core/schemas.py міряє 1..100 після normalize_name; POST /api/pricing/plastics і POST /api/catalog/items з "\u0344"*100 повертають 422 validation_error з loc на name (не 500); unit-тест у test_text.py або test_input_bounds.py; make api-check зелений. Знахідка R2-4 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** —.

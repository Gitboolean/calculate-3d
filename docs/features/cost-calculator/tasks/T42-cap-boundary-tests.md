---
id: T42
title: "Покрити межі «на межі / межа + 1» і 32/33 пластики інтеграційними й компонентними тестами"
layer: "tests"
deps: []
acs: ["AC-02", "AC-05", "AC-07"]
files_hint: ["backend/tests/integration/test_input_bounds.py", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T42 — Покрити межі «на межі / межа + 1» і 32/33 пластики інтеграційними й компонентними тестами

## Why

Follow-up з рев'ю [review-2026-10-31](../_review/review-2026-10-31.md). Критерії: AC-02, AC-05, AC-07 у [PRD §5](../PRD.md).

## Definition of Done

- [x] test_input_bounds.py: parametrize по кожному le= полю (ціна пластику, 6 налаштувань, usage_cg, print_time_s) — значення на межі приймається, на одиницю точності більше → 422 з loc цього поля; printer_lifetime_h = 1 000 000 збережено; 32 пластики приймаються, 33 → 422 на /api/costing/quote і /api/catalog/items; CalculatePage.test.tsx: 100 000 год 1 хв і 33 рядки пластику → повідомлення про межу, донату немає, збереження недоступне; make check зелений. Знахідка R4-1 у docs/features/cost-calculator/_review/review-2026-10-31.md.

## Notes

- **Blocked by:** —.

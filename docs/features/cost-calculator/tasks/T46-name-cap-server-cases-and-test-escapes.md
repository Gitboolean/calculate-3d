---
id: T46
title: "Покрити межу назви 100 символів серверними кейсами (емодзі, U+200B, U+00AD) і записати невидимі символи в бекенд-тестах як escape"
layer: "tests"
deps: []
acs: ["AC-02", "AC-11"]
files_hint: ["backend/tests/integration/test_input_bounds.py", "backend/tests/unit/test_text.py"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T46 — Покрити межу назви 100 символів серверними кейсами (емодзі, U+200B, U+00AD) і записати невидимі символи в бекенд-тестах як escape

## Why

Follow-up з рев'ю [review-2026-10-31-r5](../_review/review-2026-10-31-r5.md). Критерії: AC-02, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] test_input_bounds.py для POST /api/pricing/plastics і POST /api/catalog/items: 100 емодзі (U+1F600) збережено, 101 — 422 з полем name і нічого не записано; 100 літер + U+200B на краю збережено з назвою довжиною 100; 100 літер + U+00AD на краю прийнято; рядки 134, 187 у test_input_bounds.py і 65-66, 70-71, 75-76 у test_text.py записують U+200B, U+200D, U+0301, U+0306 як escape (\u200b, \u200d, \u0301, \u0306) без сирих невидимих символів; make api-check зелений. Знахідки R5-3, R5-8 у docs/features/cost-calculator/_review/review-2026-10-31-r5.md.

## Notes

- **Blocked by:** —.

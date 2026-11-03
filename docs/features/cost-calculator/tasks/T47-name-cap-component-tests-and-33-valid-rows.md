---
id: T47
title: "Показати межу назви біля поля компонентними тестами і будувати тест 33 рядків з валідних рядків"
layer: "ui"
deps: []
acs: ["AC-02", "AC-07", "AC-11"]
files_hint: ["web/src/pages/settings/ui/PlasticsSection.test.tsx", "web/src/features/save-item/ui/SaveItemForm.test.tsx", "web/src/pages/item/ui/ItemPage.test.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T47 — Показати межу назви біля поля компонентними тестами і будувати тест 33 рядків з валідних рядків

## Why

Follow-up з рев'ю [review-2026-10-31-r5](../_review/review-2026-10-31-r5.md). Критерії: AC-02, AC-07, AC-11 у [PRD §5](../PRD.md).

## Definition of Done

- [x] PlasticsSection.test.tsx: назва 101 емодзі → «Назва — не довше 100 символів» біля поля, жодного POST/PUT; SaveItemForm.test.tsx і ItemPage.test.tsx: назва 101 символ → повідомлення про межу біля назви, жодного POST/PUT на /api/catalog/items; CalculatePage.test.tsx:128: мок віддає 33 різні пластики, усі 33 рядки заповнено валідною витратою — «Не більше 32 пластиків в одному розрахунку», нуль POST /api/costing/quote, збереження недоступне (тест падає, якщо MAX_ROWS = 33); make web-check зелений. Знахідки R5-2, R5-6 у docs/features/cost-calculator/_review/review-2026-10-31-r5.md.

## Notes

- **Blocked by:** —.

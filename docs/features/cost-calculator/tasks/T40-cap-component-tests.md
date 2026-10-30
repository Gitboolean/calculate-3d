---
id: T40
title: "Покрити межі полів компонентними тестами на сторінках налаштувань і розрахунку"
layer: "ui"
deps: ["T39"]
acs: ["AC-02", "AC-05", "AC-07", "AC-14c"]
files_hint: ["web/src/pages/settings/ui/PlasticsSection.test.tsx", "web/src/pages/settings/ui/PriceSettingsSection.test.tsx", "web/src/pages/calculate/ui/CalculatePage.test.tsx", "web/src/pages/item/ui/ItemPage.test.tsx"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T40 — Покрити межі полів компонентними тестами на сторінках налаштувань і розрахунку

## Why

Follow-up з рев'ю [review-2026-10-30](../_review/review-2026-10-30.md). Критерії: AC-02, AC-05, AC-07, AC-14c у [PRD §5](../PRD.md).

## Definition of Done

- [ ] PlasticsSection.test.tsx: ціна 10000000,01 → повідомлення про максимум; PriceSettingsSection.test.tsx: значення понад межу для кожного обмеженого налаштування → правило з межею, збереження не відбувається; CalculatePage.test.tsx (і ItemPage.test.tsx для AC-14c): 1 000 000,01 г → «Витрата — не більше 1 000 000 г» біля рядка, внеску немає; make web-check зелений. Знахідка R3-4 у docs/features/cost-calculator/_review/review-2026-10-30.md.

## Notes

- **Blocked by:** T39.

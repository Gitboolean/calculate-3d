---
id: T39
title: "Називати межу для завеликого числа і пояснювати межу та точність в одному правилі"
layer: "ui"
deps: []
acs: ["AC-02", "AC-05", "AC-07"]
files_hint: ["web/src/shared/lib/parse-decimal.ts", "web/src/features/quote-form/model/parse.ts", "web/src/features/edit-plastic/model/validate.ts", "web/src/features/edit-price-settings/model/fields.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "todo"
---

# T39 — Називати межу для завеликого числа і пояснювати межу та точність в одному правилі

## Why

Follow-up з рев'ю [review-2026-10-30](../_review/review-2026-10-30.md). Критерії: AC-02, AC-05, AC-07 у [PRD §5](../PRD.md).

## Definition of Done

- [ ] parse-decimal повертає reason too_large для коректно записаного числа поза safe integer, і quote-form / edit-plastic / edit-price-settings показують для нього те саме повідомлення про максимум, що й для значення понад межу (10^14 г → «Витрата — не більше 1 000 000 г»); кожне поле edit-price-settings має одне правило в стилі «<Поле> — від A до B <од.> з точністю до …»; model-тести на обидва випадки; make web-check зелений. Знахідки R3-2, R3-3 у docs/features/cost-calculator/_review/review-2026-10-30.md.

## Notes

- **Blocked by:** —.

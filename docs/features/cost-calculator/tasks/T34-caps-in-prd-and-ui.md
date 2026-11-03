---
id: T34
title: "Записати верхні межі в PRD і пояснювати їх біля поля в UI"
layer: "ui"
deps: ["T33"]
acs: ["AC-02", "AC-05", "AC-07", "AC-14c"]
files_hint: ["docs/features/cost-calculator/PRD.md", "web/src/features/quote-form", "web/src/features/edit-plastic/model/validate.ts", "web/src/features/edit-price-settings/model/fields.ts"]
owner: "Anton Pohorielov"
estimate: "S"
status: "done"
---

# T34 — Записати верхні межі в PRD і пояснювати їх біля поля в UI

## Why

Follow-up з рев'ю [review-2026-10-29-r2](../_review/review-2026-10-29-r2.md). Критерії: AC-02, AC-05, AC-07, AC-14c у [PRD §5](../PRD.md).

## Definition of Done

- [ ] PRD AC-02/AC-05/AC-07 називають верхні межі з data-model.md §«Верхні межі» (замість «верхньої межі немає»); parseQuoteForm, validate.ts пластику і fields.ts налаштувань відхиляють значення понад межу з повідомленням, що називає максимум; QuoteError на validation_error показує «Перевірте поля», а не «Спробуйте ще раз»; Vitest-тести на кожне поле з межею; make web-check зелений. Знахідка R2-2 у docs/features/cost-calculator/_review/review-2026-10-29-r2.md.

## Notes

- **Blocked by:** T33.
